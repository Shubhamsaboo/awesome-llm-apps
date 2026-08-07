#!/usr/bin/env python3
"""
根据 herbs.csv 中的中药名称和URL，逐条爬取中药详情页，
提取中药信息，保存为独立txt文件。

功能特性：
  - 断点续爬：已成功爬取的条目自动跳过，通过 progress.txt 记录进度
  - 进度显示：实时显示进度条（含完成数、成功/失败数、预计剩余时间）
  - 多线程并发爬取：使用 ThreadPoolExecutor 实现，默认8线程
  - 数据解析：提取名称、来源、性味、炮制、功效、主治等结构化字段
  - 测试模式：通过 TEST_LIMIT 设置只爬取前N条，方便调试

输入/输出：
  输入：herbs.csv（由 crawl_herbs.py 生成）
  输出：中药/ 目录下，每个中药一个 .txt 文件，外加 progress.txt 进度文件

HTML解析策略（状态机）：
  中药详情页使用 card-panel 分块结构：
    - 第一个 card：名称信息 — 包含图片(figure)、h2名称、别名列表(ol.p_alternative_list)
    - 后续 card：功效信息 — 包含 h3 字段标题 + p/ul/li 正文内容
  解析器通过追踪 div 嵌套深度来识别 card 边界，在每个标签结束时
  将收集的文本片段合并为结构化块，最终由 format_herb_content 输出。

依赖：
  - 仅使用 Python 标准库（csv, urllib, ssl, html.parser, re, threading 等）
"""

import csv
import os
import urllib.request
import urllib.parse
import ssl
import re
import time
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser


# ==================== 配置 ====================
# 以脚本所在目录为基准，确保从任意工作目录运行都能正确定位输入/输出文件
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://zhongyibaike.com"
INPUT_CSV = os.path.join(SCRIPT_DIR, "herbs.csv")            # 中药列表（由 crawl_herbs.py 生成）
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "中药")                 # 输出目录，每个中药一个 .txt 文件
PROGRESS_FILE = os.path.join(OUTPUT_DIR, "progress.txt")     # 断点续爬进度文件，每行一个已完成的中药名

# 测试模式：设为正数则只爬取前N条（设为0则爬全部）
TEST_LIMIT = 0

# 并发线程数：过大会给服务器造成压力，过小则爬取效率低
MAX_WORKERS = 8

# 请求间隔（秒）：每个线程在发请求前等待，避免瞬时并发过高
# 配合 MAX_WORKERS=8，理论最大 QPS ≈ 8/1.0 = 8 req/s
REQUEST_DELAY = 1.0


# ==================== HTML 解析器 ====================
class HerbDetailParser(HTMLParser):
    """解析单个中药详情页，提取结构化数据。

    页面结构（card-panel 分块）：
      - 第一个 card：名称 — 图片(figure+figcaption)、英文名、别名列表(ol.p_alternative_list)
      - 后续 card：种植和炮制 / 效果 / 药方 — h3 字段标题 + p/ul/li 正文内容

    解析输出：
      blocks: list[tuple[str, str]] — 每个元素为 (类型标记, 文本内容)
        类型标记包括：
          - "img"  — figcaption 内的图片编号文本
          - "h2"   — 卡片中的二级标题（如"来源"、"功效"等板块标题）
          - "h3"   — 卡片中的三级标题（如"【性味】"等字段标题）
          - "p"    — 段落文本
          - "li"   — 普通列表项
          - "alt"  — 别名列表项（来自 ol.p_alternative_list）

    状态追踪机制：
      - in_content: 是否在 section#content 主内容区域内
      - in_card: 是否在 card-panel div 内部
      - card_entry_depth: 进入 card 时的 div 嵌套深度，用于识别 card 结束
      - div_depth: 当前 div 嵌套深度计数器
      - in_figure: 是否在 figure 内（figure 中非 figcaption 的文本跳过）
      - in_figcaption: 是否在 figcaption 内（图片编号文本需保留）
      - in_alt_list: 是否在别名列表 ol 内（特殊处理，标记为 "alt" 类型）
      - skip_ads: 是否在 <script> 标签内（跳过广告/脚本内容）
    """

    def __init__(self):
        super().__init__()
        self.blocks = []             # 输出块列表: [(type, text)]
        self.in_content = False      # 是否在 section#content 内
        self.in_card = False         # 是否在 card-panel div 内
        self.card_entry_depth = -1   # 进入 card-panel 时的 div 嵌套深度，用于匹配退出
        self.div_depth = 0           # 当前 div 嵌套深度（每进入 div+1，退出 div-1）
        self.in_figure = False       # 是否在 figure 内（跳过图片区域的文本）
        self.in_figcaption = False   # 是否在 figcaption 内（图片编号文本需要保留）
        self.in_h2 = False           # 是否在 h2 标签内
        self.in_h3 = False           # 是否在 h3 标签内
        self.in_p = False            # 是否在 p 标签内
        self.in_ul = False           # 是否在 ul 标签内
        self.in_ol = False           # 是否在 ol 标签内
        self.in_li = False           # 是否在 li 标签内
        self.in_alt_list = False     # 是否在别名列表 ol.p_alternative_list 内（特殊输出格式）
        self.skip_ads = False        # 是否在 <script> 标签内（跳过脚本内容）

        # 当前收集的文本片段：每次进入新的文本标签时重置，结束时合并输出
        self.current_text_frags = []  # 当前标签内的文本片段列表

    def handle_starttag(self, tag, attrs):
        """处理开始标签：进入各种状态，重置文本收集器。

        参数：
          tag: 标签名
          attrs: 属性列表，每个元素为 (属性名, 属性值)
        """
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")

        # 检测是否进入主内容区域
        if tag == "section" and attrs_dict.get("id") == "content":
            self.in_content = True
        if not self.in_content:
            return

        # div 嵌套深度追踪 — 每进入一个 div 深度+1
        if tag == "div":
            self.div_depth += 1
            # 检测是否进入 card-panel — 这是页面内容的核心容器
            if "card-panel" in cls:
                self.in_card = True
                self.card_entry_depth = self.div_depth  # 记录进入深度，后续通过深度匹配识别退出

        # figure/figurecaption：图片和图片说明区域
        if tag == "figure":
            self.in_figure = True
        if tag == "figcaption" and self.in_figure:
            self.in_figcaption = True
            self.current_text_frags = []  # 开始收集 figcaption 内的文本（图片编号）

        # 文本标签：仅在 card 内部且不在 figure 内时处理
        if tag == "h2" and self.in_card and not self.in_figure:
            self.in_h2 = True
            self.current_text_frags = []  # 重置文本片段收集器
        if tag == "h3" and self.in_card and not self.in_figure:
            self.in_h3 = True
            self.current_text_frags = []
        if tag == "p" and self.in_card and not self.in_figure:
            self.in_p = True
            self.current_text_frags = []
        if tag == "ul" and self.in_card and not self.in_figure:
            self.in_ul = True
        if tag == "ol" and self.in_card and not self.in_figure:
            self.in_ol = True
            # 检测是否为别名列表容器，别名列表用特殊格式输出
            if "p_alternative_list" in cls:
                self.in_alt_list = True
        if tag == "li" and self.in_card and not self.in_figure:
            self.in_li = True
            self.current_text_frags = []
        # 跳过 <script> 标签内的内容（广告脚本等）
        if tag == "script":
            self.skip_ads = True

    def handle_endtag(self, tag):
        """处理结束标签：合并文本片段为块，恢复状态。

        参数：
          tag: 结束标签名

        关键逻辑：
          - figcaption/h2/h3/p/li 结束时，将收集的文本片段合并为一个完整文本，
            生成对应的输出块，然后清空文本片段收集器
          - div 结束时检查是否退出了当前 card（通过深度匹配判断）
        """
        if not self.in_content:
            return

        # 退出主内容区域
        if tag == "section":
            self.in_content = False

        # 退出 figure 及其子元素
        if tag == "figure":
            self.in_figure = False
        if tag == "figcaption":
            self.in_figcaption = False
            # 汇总 figcaption 内的所有文本片段
            text = "".join(self.current_text_frags).strip()
            if text:
                # 去掉所有空白字符，如 "1 #" -> "1#"，保持编号整洁
                cleaned = re.sub(r'\s+', '', text)
                if cleaned:
                    self.blocks.append(("img", cleaned))
            self.current_text_frags = []  # 清空，防止外层标签复用

        # 退出文本标签：合并文本片段，生成输出块
        if tag == "h2" and self.in_h2:
            self.in_h2 = False
            text = "".join(self.current_text_frags).strip()
            if text:
                self.blocks.append(("h2", text))
        if tag == "h3" and self.in_h3:
            self.in_h3 = False
            text = "".join(self.current_text_frags).strip()
            if text:
                self.blocks.append(("h3", text))
        if tag == "p" and self.in_p:
            self.in_p = False
            text = "".join(self.current_text_frags).strip()
            if text:
                self.blocks.append(("p", text))
        if tag == "li" and self.in_li:
            self.in_li = False
            text = "".join(self.current_text_frags).strip()
            if text:
                # 别名列表项用 "alt" 类型标记，后续格式化时加前缀
                if self.in_alt_list:
                    self.blocks.append(("alt", text))
                else:
                    self.blocks.append(("li", text))
            self.current_text_frags = []  # 清空，防止外层标签复用

        # 退出容器标签
        if tag == "ul":
            self.in_ul = False
        if tag == "ol":
            self.in_ol = False
            self.in_alt_list = False  # ol 结束时退出别名列表状态
        if tag == "div":
            # 深度匹配：当 div_depth 回退到进入 card 时的深度时，说明退出了该 card
            if self.in_card and self.div_depth == self.card_entry_depth:
                self.in_card = False
                self.card_entry_depth = -1
            self.div_depth -= 1  # 每退出一个 div，深度-1
        if tag == "script":
            self.skip_ads = False

    def handle_data(self, data):
        """处理文本数据：在特定标签内收集文本片段。

        参数：
          data: 原始文本内容

        收集策略：
          - 跳过非内容区域的文本
          - 跳过 <script> 内的文本（广告/脚本）
          - 跳过 figure 内非 figcaption 的文本（如图片 alt 文本）
          - 对 figcaption/h2/h3/p/li 内的文本，追加到 current_text_frags，
            在对应的 handle_endtag 中统一合并输出
        """
        if not self.in_content or self.skip_ads:
            return

        # 跳过 figure 内的非 figcaption 文本（如 <img> 的 alt 属性等）
        if self.in_figure and not self.in_figcaption:
            return

        # figcaption, h2, h3, p, li 内的文本 — 全部用统一方式收集
        # handle_endtag 中会合并这些片段并生成输出块
        if self.in_figcaption or self.in_h2 or self.in_h3 or self.in_p or self.in_li:
            self.current_text_frags.append(data)


# ==================== 输出格式化 ====================
def format_herb_content(blocks):
    """将解析出的块列表格式化为最终的可读文本。

    参数：
      blocks: list[tuple[str, str]] — HerbDetailParser 解析出的块列表

    返回：
      str — 格式化后的文本内容

    格式化规则：
      - "img" 块：直接输出图片编号文本
      - "h2" 块：作为板块标题，前面加空行与上一板块分隔
      - "h3" 块：作为字段标题，紧跟前一个块输出
      - "p" 块：作为段落正文；如果以【开头为子标题格式，不额外处理
      - "alt" 块：别名列表项，前面加 "- " 前缀
      - "li" 块：普通列表项，直接输出
    """
    lines = []
    for block_type, text in blocks:
        if block_type == "img":
            lines.append(text)
        elif block_type == "h2":
            # 板块标题前加空行，与上一板块形成视觉分隔
            if lines:
                lines.append("")
            lines.append(text)
        elif block_type == "h3":
            lines.append(text)
        elif block_type == "p":
            # 段落正文，可能以【】格式内嵌子标题（如【性味】）
            lines.append(text)
        elif block_type == "alt":
            # 别名列表项以 "- " 前缀输出，便于阅读
            lines.append(f"- {text}")
        elif block_type == "li":
            lines.append(text)

    return "\n".join(lines).strip()


# ==================== 网络请求 ====================
def fetch_page(url):
    """获取页面HTML内容（自动处理URL中的中文字符）。

    参数：
      url: 目标页面的完整URL（可能含中文）

    返回：
      str — 页面的HTML文本，使用UTF-8（或服务端指定的编码）解码

    说明：
      - URL中文路径编码：使用 urllib.parse.quote 对路径中的中文字符进行
        百分号编码，确保请求能被正确路由
      - SSL证书验证被关闭，兼容目标网站的证书配置
      - 设置合理的请求头和30秒超时
    """
    # 将URL中的中文路径进行编码：先解析URL各部分，对路径单独编码再重组
    parsed = urllib.parse.urlparse(url)
    encoded_path = urllib.parse.quote(parsed.path, safe="/:")
    safe_url = urllib.parse.urlunparse(parsed._replace(path=encoded_path))

    # SSL上下文：关闭证书验证
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        safe_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        },
    )
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        # 从响应头推断字符编码，默认UTF-8
        content_type = resp.headers.get("Content-Type", "")
        charset = "utf-8"
        if "charset=" in content_type:
            charset = content_type.split("charset=")[-1].strip()
        html_bytes = resp.read()
        return html_bytes.decode(charset, errors="replace")


# ==================== 进度管理（断点续爬） ====================
# 保护 progress.txt 的并发写入，确保多线程环境下不会交错写入
_progress_lock = threading.Lock()


def load_progress():
    """加载已完成爬取的中药名称集合。

    返回：
      set[str] — 已成功爬取的中药名称集合，用于断点续爬时过滤

    读取 progress.txt 文件，每行一个中药名，空行被忽略。
    如果文件不存在则返回空集合。
    """
    if not os.path.exists(PROGRESS_FILE):
        return set()
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_progress(name):
    """线程安全地记录一个已完成爬取的中药。

    参数：
      name: 中药名称，将被追加写入 progress.txt

    线程安全保证：
      使用 _progress_lock（threading.Lock）确保并发写入时各行完整，
      不会出现两个线程的写入内容交错的情况。
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with _progress_lock:
        with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
            f.write(name + "\n")


# ==================== 主流程 ====================
def sanitize_filename(name):
    """将中药名转为安全的文件名。

    参数：
      name: 原始中药名称（可能含文件系统非法字符）

    返回：
      str — 清理后的安全文件名

    处理：将 / \ : * ? " < > | 等文件系统非法字符替换为下划线。
    """
    illegal_chars = r'[\\/:*?"<>|]'
    safe = re.sub(illegal_chars, '_', name)
    return safe.strip()


def crawl_one(name, url):
    """爬取单个中药详情页并保存为txt文件。

    参数：
      name: 中药名称
      url: 中药详情页的完整URL

    返回：
      tuple[str, bool, str] — (中药名称, 是否成功, 状态消息)

    流程：
      1. 等待 REQUEST_DELAY 秒（控制请求速率）
      2. 发送HTTP请求获取页面HTML
      3. 用 HerbDetailParser 解析HTML提取结构化数据
      4. 用 format_herb_content 格式化为可读文本
      5. 写入 中药/{安全文件名}.txt
      6. 记录到 progress.txt（成功时）

    错误处理：任何异常都会被捕获，返回失败状态和错误消息，
    不会中断整个批量爬取流程。
    """
    try:
        # 每个线程在发起请求前等待，确保多线程下的总请求速率可控
        # 8线程 × 1秒间隔 → 实际QPS约为 8/秒（每秒最多同时发出8个请求）
        time.sleep(REQUEST_DELAY)
        html = fetch_page(url)
        parser = HerbDetailParser()
        parser.feed(html)  # 将HTML喂给解析器，触发状态机
        content = format_herb_content(parser.blocks)
        if not content:
            return (name, False, "⚠ 解析内容为空")

        safe_name = sanitize_filename(name)
        filepath = os.path.join(OUTPUT_DIR, f"{safe_name}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            # 文件头部写入元信息
            f.write(f"【中药名称】{name}\n")
            f.write(f"- 中医百科\n")
            f.write(f"- {name}\n")
            f.write(content)

        # 成功后记录进度，支持断点续爬
        save_progress(name)
        return (name, True, "✓")
    except Exception as e:
        # 捕获所有异常，不影响其他条目的爬取
        return (name, False, f"✗ 爬取失败: {e}")


def main():
    """主入口：读取中药列表 -> 过滤已完成 -> 多线程并发爬取 -> 输出统计。

    运行流程：
      1. 读取 herbs.csv 获取全部中药名称和URL
      2. 如果设置了 TEST_LIMIT > 0，只取前N条（测试模式）
      3. 加载 progress.txt，过滤掉已成功爬取的条目（断点续爬）
      4. 创建 ThreadPoolExecutor 线程池，提交所有待爬取任务
      5. 实时显示进度条（完成数、成功数、失败数、预计剩余时间）
      6. 所有任务完成后打印汇总统计
    """
    # 读取中药列表
    if not os.path.exists(INPUT_CSV):
        print(f"错误: 找不到 {INPUT_CSV}，请先运行 crawl_herbs.py")
        sys.exit(1)

    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        all_herbs = [(row["中药名称"], row["中药名称对应的URL"]) for row in reader]

    total_all = len(all_herbs)
    print(f"共读取到 {total_all} 个中药条目")

    # 测试模式：限制爬取数量，方便调试解析逻辑
    if TEST_LIMIT > 0:
        all_herbs = all_herbs[:TEST_LIMIT]
        print(f"🔧 测试模式：只爬取前 {TEST_LIMIT} 条")

    # 加载断点，过滤已完成的 — 实现断点续爬的核心逻辑
    completed = load_progress()
    herbs = [(name, url) for name, url in all_herbs if name not in completed]
    skip_count = len(all_herbs) - len(herbs)
    if skip_count > 0:
        print(f"📌 断点续爬：跳过已完成 {skip_count} 条")
    print(f"待爬取: {len(herbs)} 条，并发线程: {MAX_WORKERS}\n")

    if not herbs:
        print("所有条目已完成，无需爬取。")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ===== 线程安全的统计与进度显示 =====
    # stats_lock 保护 stats 字典和进度条输出，防止多线程交错打印
    stats_lock = threading.Lock()
    stats = {"success": 0, "fail": 0, "done": 0}
    total = len(herbs)
    start_time = time.time()

    def print_progress(name, ok, msg):
        """线程安全地打印进度条和状态信息。

        参数：
          name: 当前处理的中药名称
          ok: 是否爬取成功
          msg: 状态消息（成功时显示✓，失败时显示错误详情）

        线程安全保证：
          使用 stats_lock 确保 stats 更新和终端输出的原子性，
          避免多线程同时写入导致进度条显示混乱。

        输出内容：
          [████████░░░░░░░░░░░░] 进度/总数 (百分比) | 成功数 失败数 跳过数 [预计剩余] | 状态
        """
        with stats_lock:
            if ok:
                stats["success"] += 1
            else:
                stats["fail"] += 1
            stats["done"] += 1
            done = stats["done"]
            success = stats["success"]
            fail = stats["fail"]

            # 构造进度条：[████████░░░░░░░░░░░░]
            percent = (done / total) * 100
            bar_len = 30
            filled = int(bar_len * done // total)
            bar = "█" * filled + "░" * (bar_len - filled)

            # 预估剩余时间（基于已完成条目的平均耗时）
            elapsed = time.time() - start_time
            eta = ""
            if done > 0:
                avg_time = elapsed / done  # 每条平均耗时
                remaining = total - done
                eta_sec = avg_time * remaining
                if eta_sec > 60:
                    eta = f" | 预计剩余 {eta_sec / 60:.1f} 分钟"
                else:
                    eta = f" | 预计剩余 {eta_sec:.0f} 秒"

            # 使用 \r 回到行首实现进度条原地刷新
            status = "✓" if ok else "✗"
            sys.stdout.write(
                f"\r[{bar}] {done}/{total} ({percent:.1f}%) "
                f"| ✓{success} ✗{fail} ⏭{skip_count}{eta}  "
                f"| {status} {name} "
            )
            sys.stdout.flush()
            # 失败信息换行打印，避免覆盖进度条
            if not ok:
                sys.stdout.write(f"\n  {msg}\n")
                sys.stdout.flush()

    # ===== 线程池并发爬取 =====
    # 使用 ThreadPoolExecutor 管理线程池，as_completed 按完成顺序处理结果
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 一次性提交所有任务，返回 future 到 (name, url) 的映射
        futures = {
            executor.submit(crawl_one, name, url): (name, url)
            for name, url in herbs
        }
        # as_completed 按任务完成顺序（而非提交顺序）返回 future
        for future in as_completed(futures):
            name, ok, msg = future.result()
            print_progress(name, ok, msg)

    # ===== 最终统计 =====
    elapsed_total = time.time() - start_time
    print(f"\n\n{'=' * 50}")
    print(f"爬取完成！")
    print(f"  成功: {stats['success']} 条")
    print(f"  失败: {stats['fail']} 条")
    print(f"  跳过(断点): {skip_count} 条")
    print(f"  总计: {total_all} 条")
    print(f"  并发线程: {MAX_WORKERS}")
    print(f"  耗时: {elapsed_total:.1f} 秒")
    if stats['success'] > 0:
        print(f"  平均每条: {elapsed_total / stats['success']:.1f} 秒")
    print(f"  输出目录: {os.path.abspath(OUTPUT_DIR)}/")


if __name__ == "__main__":
    main()
