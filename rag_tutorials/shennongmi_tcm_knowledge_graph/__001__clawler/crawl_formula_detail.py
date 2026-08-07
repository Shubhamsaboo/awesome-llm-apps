#!/usr/bin/env python3
"""
根据 formulas.csv 中的方剂名称和URL，逐条爬取方剂详情页，
提取药方信息，保存为独立txt文件。

功能特性：
  - 断点续爬：已成功爬取的条目自动跳过，通过 progress.txt 记录进度
  - 进度显示：实时显示进度条（含完成数、成功/失败数、预计剩余时间）
  - 多线程并发爬取：使用 ThreadPoolExecutor 实现，默认8线程
  - 数据解析：提取出处、分类、组成、功用、主治、用法、注意等结构化字段
  - 测试模式：通过 TEST_LIMIT 设置只爬取前N条，方便调试

输入/输出：
  输入：formulas.csv（由 crawl_formulas.py 生成）
  输出：方剂/ 目录下，每个方剂一个 .txt 文件，外加 progress.txt 进度文件

HTML解析策略（状态机）：
  方剂详情页使用 card-panel 分块结构，每个 card 包含：
    - h2：板块标题（如"药方"、"功效"等）
    - h3：字段标题（如"出处"、"分类"、"组成"等）
    - p / li：字段正文（段落或列表项）
  解析器通过追踪 card 的开始/结束来组织数据，最终输出为两级结构：
  （板块标题 -> [(字段标题, 字段内容)]）

与 crawl_herb_detail.py 的差异：
  - 数据结构不同：方剂页是"板块-字段"两级结构，中药页是扁平块列表
  - 解析器使用 FormulaDetailParser，内部维护 sections 列表（两级结构）
  - 提供了 _flush_field 和 _flush_paragraph 辅助方法来管理文本缓冲

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
INPUT_CSV = os.path.join(SCRIPT_DIR, "formulas.csv")        # 方剂列表（由 crawl_formulas.py 生成）
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "方剂")                # 输出目录，每个方剂一个 .txt 文件
PROGRESS_FILE = os.path.join(OUTPUT_DIR, "progress.txt")    # 断点续爬进度文件，每行一个已完成的方剂名

# 测试模式：设为正数则只爬取前N条（设为0则爬全部）
TEST_LIMIT = 0

# 并发线程数：过大会给服务器造成压力，过小则爬取效率低
MAX_WORKERS = 8

# 请求间隔（秒）：每个线程在发请求前等待，避免瞬时并发过高
# 配合 MAX_WORKERS=8，理论最大 QPS ≈ 8/1.0 = 8 req/s
REQUEST_DELAY = 1.0


# ==================== HTML 解析器 ====================
class FormulaDetailParser(HTMLParser):
    """解析单个方剂详情页，提取结构化数据。

    页面结构（card-panel 两级分块）：
      每个 card-panel div 代表一个板块，包含：
        - h2：板块标题（如"药方"、"功效"、"使用注意"等）
        - h3：字段标题（如"出处"、"分类"、"组成"、"功用"、"主治"等）
        - p 或 li：字段正文内容（可能跨多个段落或列表项）

    解析输出：
      sections: list[tuple[str, list[tuple[str, str]]]]
        每个元素为 (板块标题, [(字段标题, 字段内容), ...])
        例如：[("药方", [("出处", "..."), ("分类", "..."), ...]),
               ("功效", [("功用", "..."), ("主治", "..."), ...])]

    内部状态追踪：
      - in_content: 是否在 section#content 内
      - in_card: 是否在 card-panel div 内
      - in_h2/h3/p/li: 当前所在标签类型
      - skip_ads: 是否在 <script> 内（跳过广告脚本）

    缓冲管理：
      - current_card_title: 当前 card 的板块标题（来自 h2）
      - current_field: 当前字段标题（来自 h3），可能为 None 或空字符串
      - current_paragraphs: 当前字段下的所有段落列表
      - current_para_frags: 当前段落内的文本片段列表（handle_data 中累积）
      - current_card_content: 当前 card 下的所有 (字段标题, 内容) 列表
    """

    def __init__(self):
        super().__init__()
        # === 输出数据 ===
        self.sections = []          # 最终输出: [(标题, [(子标题, 内容)])]

        # === 当前 card 的缓冲数据 ===
        self.current_card_title = None      # 当前 card 的 h2 标题
        self.current_field = None           # 当前字段的 h3 标题
        self.current_paragraphs = []        # 当前字段下的段落列表，每个元素是一个完整段落
        self.current_para_frags = []        # 当前段落内的文本片段（在 handle_data 中累积）
        self.current_card_content = []      # 当前 card 下的所有字段: [(field_name, content)]

        # === 状态追踪标志位 ===
        self.in_card = False     # 是否在 card-panel div 内
        self.in_h2 = False       # 是否在 h2 标签内
        self.in_h3 = False       # 是否在 h3 标签内
        self.in_p = False        # 是否在 p 标签内
        self.in_li = False       # 是否在 li 标签内
        self.in_content = False  # 是否在 section#content 主内容区域内
        self.skip_ads = False    # 是否在 <script> 标签内（跳过广告/脚本）

    def handle_starttag(self, tag, attrs):
        """处理开始标签：进入各种状态，管理缓冲。

        参数：
          tag: 标签名
          attrs: 属性列表
        """
        attrs_dict = dict(attrs)

        # 检测是否进入主内容区域
        if tag == "section" and attrs_dict.get("id") == "content":
            self.in_content = True

        if not self.in_content:
            return

        # 检测 card-panel：页面的核心数据容器，每个 card = 一个板块
        if tag == "div" and "card-panel" in attrs_dict.get("class", ""):
            self.in_card = True
            self.current_card_content = []  # 新 card 开始，重置字段缓存

        # h2：板块标题（如"药方"、"功效"）
        if tag == "h2" and self.in_card:
            self.in_h2 = True
        # h3：字段标题（如"出处"、"组成"），遇到新 h3 先把上一个字段存下来
        if tag == "h3" and self.in_card:
            self.in_h3 = True
            self._flush_field()  # 保存上一个字段的内容到 current_card_content
        # p：段落内容，开始新段落
        if tag == "p" and self.in_card:
            self.in_p = True
            self.current_para_frags = []  # 新段落开始，重置片段缓冲
        # li：列表项内容，开始新段落
        if tag == "li" and self.in_card:
            self.in_li = True
            self.current_para_frags = []  # 新段落开始，重置片段缓冲
        # script：广告/脚本，跳过内部文本
        if tag == "script" and self.in_card:
            self.skip_ads = True

    def _flush_field(self):
        """将当前累积的字段内容存入 card 的内容列表。

        这是解析器的核心辅助方法，在以下时机调用：
          - 遇到新的 h3 时（保存上一个字段）
          - card 结束时（保存最后一个字段）

        工作流程：
          1. 先刷新当前段落（将 current_para_frags 合并到 current_paragraphs）
          2. 如果当前字段有标题且有内容，存入 current_card_content
          3. 重置字段和数据缓冲
        """
        # 先保存当前段落 — 确保所有文本片段都被合并
        self._flush_paragraph()
        if self.current_field and self.current_paragraphs:
            # 将段落列表用换行符连接为完整内容
            text = "\n".join(self.current_paragraphs)
            if text:
                self.current_card_content.append((self.current_field, text))
        # 重置字段标题和段落缓冲，为下一个字段做准备
        self.current_field = None
        self.current_paragraphs = []

    def _flush_paragraph(self):
        """将当前段落片段合并为一个完整段落。

        在以下时机调用：
          - p/li 标签结束时（段落结束）
          - _flush_field 中（字段结束时保存最后一个段落）
        """
        text = "".join(self.current_para_frags).strip()
        if text:
            self.current_paragraphs.append(text)
        self.current_para_frags = []

    def handle_endtag(self, tag):
        """处理结束标签：刷新缓冲，存储数据，恢复状态。

        参数：
          tag: 结束标签名
        """
        if not self.in_content:
            return

        # 退出主内容区域
        if tag == "section":
            self.in_content = False

        # 退出文本标签：h2/h3 清除标志位，p/li 刷新段落缓冲
        if tag == "h2" and self.in_h2:
            self.in_h2 = False
        if tag == "h3" and self.in_h3:
            self.in_h3 = False
        if tag == "p" and self.in_p:
            self.in_p = False
            self._flush_paragraph()  # 段落结束，将片段合并为完整段落
        if tag == "li" and self.in_li:
            self.in_li = False
            self._flush_paragraph()  # 列表项结束，将片段合并为完整段落
        # card 结束：保存最后一个字段，将整个 card 的数据存入 sections
        if tag == "div" and self.in_card:
            self.in_card = False
            self._flush_field()  # card 结束前保存最后一个字段
            if self.current_card_title and self.current_card_content:
                self.sections.append((self.current_card_title, self.current_card_content))
            self.current_card_title = None
        # script 结束：恢复文本收集
        if tag == "script":
            self.skip_ads = False

    def handle_data(self, data):
        """处理文本数据：根据当前标签类型分发文本。

        参数：
          data: 原始文本内容

        分发逻辑：
          - 在 h2 内：作为板块标题赋值给 current_card_title
          - 在 h3 内：作为字段标题赋值给 current_field（触发 _flush_field）
          - 在 p 或 li 内：追加到 current_para_frags（可能跨多次调用）
          - 在 script 内：跳过
          - 不在 card 内：跳过
        """
        if not self.in_content:
            return
        if self.skip_ads:
            return

        text = data.strip()
        if not text:
            return

        # h2 文本 → 板块标题（保留原始标题，用于区分"药方"和"功效"等不同板块）
        if self.in_h2 and self.in_card:
            self.current_card_title = text
        # h3 文本 → 字段标题（上一个字段已在 handle_starttag 的 _flush_field 中保存）
        elif self.in_h3 and self.in_card:
            self.current_field = text
            self.current_paragraphs = []  # 新字段，重置段落列表
        # p 或 li 文本 → 字段正文内容，追加到当前段落的文本片段
        elif (self.in_p or self.in_li) and self.in_card:
            # 如果该字段没有 h3 标题，使用空字符串作为字段名
            if not self.current_field:
                self.current_field = ""
            # 同一段落内的文本片段直接拼接（HTML中的文本可能被其他内联标签切割）
            self.current_para_frags.append(data)


# ==================== 输出格式化 ====================
def parse_formula_detail(html):
    """解析方剂详情页HTML，返回格式化文本。

    参数：
      html: 方剂详情页的HTML字符串

    返回：
      str — 格式化后的文本内容，格式为：
        板块标题1
        字段标题1
        字段内容1
        字段标题2
        字段内容2
        <空行>
        板块标题2
        ...

    这是 crawl_formula_detail.py 的顶层解析入口，封装了
    FormulaDetailParser 的创建、HTML 喂入和结果格式化。
    """
    parser = FormulaDetailParser()
    parser.feed(html)

    lines = []
    for section_title, fields in parser.sections:
        # 板块标题
        lines.append(section_title)
        for field_name, content in fields:
            # 字段标题，紧跟前一行
            lines.append(field_name)
            # 字段内容（可能多行）
            lines.append(content)
        # 板块间以空行分隔
        lines.append("")

    return "\n".join(lines).strip()


# ==================== 网络请求 ====================
def fetch_page(url):
    """获取页面HTML内容（自动处理URL中的中文字符）。

    参数：
      url: 目标页面的完整URL（可能含中文）

    返回：
      str — 页面的HTML文本

    说明：
      - URL中文路径编码：使用 urllib.parse.quote 对路径中的中文字符进行
        百分号编码，确保请求能被正确路由
      - SSL证书验证被关闭，兼容目标网站的证书配置
      - 设置合理的请求头（包括中文 Accept-Language）和30秒超时
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
    """加载已完成爬取的方剂名称集合。

    返回：
      set[str] — 已成功爬取的方剂名称集合，用于断点续爬时过滤

    读取 progress.txt 文件，每行一个方剂名，空行被忽略。
    如果文件不存在则返回空集合。
    """
    if not os.path.exists(PROGRESS_FILE):
        return set()
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_progress(name):
    """线程安全地记录一个已完成爬取的方剂。

    参数：
      name: 方剂名称，将被追加写入 progress.txt

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
    """将方剂名转为安全的文件名。

    参数：
      name: 原始方剂名称（可能含文件系统非法字符）

    返回：
      str — 清理后的安全文件名

    处理：将 / \ : * ? " < > | 等文件系统非法字符替换为下划线。
    """
    illegal_chars = r'[\\/:*?"<>|]'
    safe = re.sub(illegal_chars, '_', name)
    return safe.strip()


def crawl_one(name, url):
    """爬取单个方剂详情页并保存为txt文件。

    参数：
      name: 方剂名称
      url: 方剂详情页的完整URL

    返回：
      tuple[str, bool, str] — (方剂名称, 是否成功, 状态消息)

    流程：
      1. 等待 REQUEST_DELAY 秒（控制请求速率，避免给服务器压力）
      2. 发送HTTP请求获取页面HTML
      3. 用 FormulaDetailParser + parse_formula_detail 解析提取数据
      4. 写入 方剂/{安全文件名}.txt（含元信息头部）
      5. 记录到 progress.txt（成功时）

    错误处理：任何异常都会被捕获，返回失败状态和错误消息，
    不会中断整个批量爬取流程。
    """
    try:
        # 每个线程在发起请求前等待，确保多线程下的总请求速率可控
        # 8线程 × 1秒间隔 → 实际QPS约为 8/秒（每秒最多同时发出8个请求）
        time.sleep(REQUEST_DELAY)
        html = fetch_page(url)
        content = parse_formula_detail(html)
        if not content:
            return (name, False, "⚠ 解析内容为空")

        safe_name = sanitize_filename(name)
        filepath = os.path.join(OUTPUT_DIR, f"{safe_name}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            # 文件头部写入元信息，方便后续处理识别
            f.write(f"【方剂名称】{name}\n")
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
    """主入口：读取方剂列表 -> 过滤已完成 -> 多线程并发爬取 -> 输出统计。

    运行流程：
      1. 读取 formulas.csv 获取全部方剂名称和URL
      2. 如果设置了 TEST_LIMIT > 0，只取前N条（测试模式，方便调试）
      3. 加载 progress.txt，过滤掉已成功爬取的条目（实现断点续爬）
      4. 创建 ThreadPoolExecutor 线程池，提交所有待爬取任务
      5. 使用 as_completed 按完成顺序接收结果，实时更新进度条
      6. 所有任务完成后打印汇总统计（成功/失败/跳过/耗时等）
    """
    # 读取方剂列表
    if not os.path.exists(INPUT_CSV):
        print(f"错误: 找不到 {INPUT_CSV}，请先运行 crawl_formulas.py")
        sys.exit(1)

    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        all_formulas = [(row["方剂名称"], row["方剂名称的URL"]) for row in reader]

    total_all = len(all_formulas)
    print(f"共读取到 {total_all} 个方剂条目")

    # 测试模式：限制爬取数量，方便调试解析逻辑
    if TEST_LIMIT > 0:
        all_formulas = all_formulas[:TEST_LIMIT]
        print(f"🔧 测试模式：只爬取前 {TEST_LIMIT} 条")

    # 加载断点，过滤已完成的 — 实现断点续爬的核心逻辑
    completed = load_progress()
    formulas = [(name, url) for name, url in all_formulas if name not in completed]
    skip_count = len(all_formulas) - len(formulas)
    if skip_count > 0:
        print(f"📌 断点续爬：跳过已完成 {skip_count} 条")
    print(f"待爬取: {len(formulas)} 条，并发线程: {MAX_WORKERS}\n")

    if not formulas:
        print("所有条目已完成，无需爬取。")
        return

    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ===== 线程安全的统计与进度显示 =====
    # stats_lock 保护 stats 字典和进度条的终端输出，
    # 确保多线程环境下打印内容不会交错混乱
    stats_lock = threading.Lock()
    stats = {"success": 0, "fail": 0, "done": 0}
    total = len(formulas)
    start_time = time.time()

    def print_progress(name, ok, msg):
        """线程安全地打印进度条和状态信息。

        参数：
          name: 当前处理的方剂名称
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
            for name, url in formulas
        }
        # as_completed 按任务完成顺序（而非提交顺序）返回 future，
        # 这样先完成的任务先显示结果，不阻塞
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
