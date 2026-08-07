#!/usr/bin/env python3
"""
爬取中医方剂百科（https://zhongyibaike.com/wiki/中医方剂）的所有方剂名称和URL，
保存为CSV文件。

整体流程：
  1. 构造目标页面的完整URL（自动对中文路径进行编码）
  2. 通过 HTTP GET 请求获取页面 HTML
  3. 使用自定义的 FormulaParser（基于 HTMLParser）解析 HTML，提取方剂名称和链接
  4. 对提取结果按URL去重（保留首次出现的顺序）
  5. 将去重后的（方剂名称, URL）列表写入 CSV 文件

与 crawl_herbs.py 的差异：
  - 目标页面路径不同（/wiki/中医方剂 vs /wiki/中药大全）
  - 输出文件名不同（formulas.csv vs herbs.csv）
  - 解析器内部变量命名改为 formula 相关，逻辑结构完全相同

依赖：
  - 仅使用 Python 标准库（csv, urllib, ssl, html.parser），无需安装第三方包
"""

import csv
import os
import urllib.request
import urllib.parse
import ssl
from html.parser import HTMLParser


# ==================== 全局配置 ====================
# 以脚本所在目录为基准，确保从任意工作目录运行都能正确定位输出文件
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://zhongyibaike.com"
PAGE_PATH = "/wiki/中医方剂"
# 对URL中的中文路径进行编码，避免请求时因非ASCII字符导致问题
PAGE_URL = BASE_URL + urllib.parse.quote(PAGE_PATH, safe="/:")
OUTPUT_CSV = os.path.join(SCRIPT_DIR, "formulas.csv")


# ==================== HTML 解析器 ====================
class FormulaParser(HTMLParser):
    """解析中医方剂页面的HTML，提取方剂名称和URL。

    解析策略（基于状态机）：
      1. 通过 section#content 定位主内容区域，忽略页面的导航栏、页脚等无关部分
      2. 在内容区域内，找到所有以 /wiki/ 开头的 <a> 链接
      3. 每个 <a> 标签的文本内容即为方剂名称，href 属性即为相对URL
      4. 在 handle_data 中提取名称后立即重置 current_a_href，避免同一标签重复提取

    属性说明：
      formulas: list[tuple[str, str]] — 最终输出的（方剂名称, 完整URL）列表
      current_tag_stack: list[str] — 当前打开的标签栈，用于跟踪嵌套层级
      inside_content: bool — 标志位，表示当前解析位置是否在 section#content 内部
      current_a_href: str|None — 当前正在处理的 <a> 标签的 href 值；在 handle_data
                               提取名称后立即置空，防止同一个链接内的多个文本片段
                               都被记录
    """

    def __init__(self):
        super().__init__()
        self.formulas = []          # 存储 (方剂名称, 完整URL)
        self.current_tag_stack = []  # 当前标签栈，跟踪进入/退出标签的嵌套关系
        self.inside_content = False  # 是否在 section#content 内
        self.current_a_href = None  # 当前 <a> 标签的 href，非None表示正在处理一个有效链接

    def handle_starttag(self, tag, attrs):
        """处理开始标签：跟踪进入主内容区域和有效链接。

        参数：
          tag: 标签名（如 'a', 'section', 'div'）
          attrs: 属性列表，每个元素为 (属性名, 属性值) 元组
        """
        attrs_dict = dict(attrs)

        # 检测是否进入了主内容区域 — section#content 是页面的正文容器
        if tag == "section" and attrs_dict.get("id") == "content":
            self.inside_content = True

        if self.inside_content:
            # 记录进入的标签，用于跟踪嵌套层级（虽然当前逻辑未深度使用栈）
            self.current_tag_stack.append(tag)
            if tag == "a":
                href = attrs_dict.get("href", "")
                # 只取 /wiki/ 开头的内部链接，过滤掉外部链接、锚点、编辑链接等
                if href.startswith("/wiki/"):
                    self.current_a_href = href

    def handle_endtag(self, tag):
        """处理结束标签：管理内容区域退出和标签栈弹出。

        参数：
          tag: 结束标签名
        """
        if self.inside_content:
            # 退出 section#content 主内容区域，同时清空标签栈
            if tag == "section":
                self.inside_content = False
                self.current_tag_stack.clear()
            elif self.current_tag_stack and self.current_tag_stack[-1] == tag:
                self.current_tag_stack.pop()

            # 处理 </a> 结束标签：如果当前有未提取名称的链接，消费掉
            # （这种情况发生在 <a> 内没有文本节点时，比如嵌套了 <img> 等元素）
            if tag == "a" and self.current_a_href:
                self.current_a_href = None

    def handle_data(self, data):
        """处理文本数据：当在有效链接内时提取文本作为方剂名称。

        参数：
          data: 原始文本内容（可能包含空白字符）

        关键点：提取名称后立即将 current_a_href 置为 None，这样即使
        HTML 中有多个文本片段在同一个 <a> 内（如 <a>文字1<br>文字2</a>），
        也只会取到第一个有效文本，后续文本会被忽略。这符合中医方剂页面的
        实际结构（每个链接内只有一个名称文本）。
        """
        if self.inside_content and self.current_a_href:
            name = data.strip()
            if name:
                full_url = BASE_URL + self.current_a_href
                self.formulas.append((name, full_url))
                # 重置，防止同一个 a 标签重复记录
                self.current_a_href = None


# ==================== 网络请求 ====================
def fetch_page(url):
    """获取页面HTML内容。

    参数：
      url: 目标页面的完整URL（已编码）

    返回：
      str — 页面的HTML文本，使用UTF-8（或服务端指定的编码）解码

    说明：
      - SSL证书验证被关闭（check_hostname=False, CERT_NONE），因为目标网站
        可能使用自签名证书或证书配置不完整
      - 设置合理的 User-Agent 和 Accept 头，模拟浏览器行为，避免被反爬
      - 超时设为30秒，避免无限等待
    """
    # 创建SSL上下文，关闭证书验证以兼容自签名/过期证书的网站
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        url,
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
        # 从响应头的 Content-Type 中提取字符编码，默认使用 UTF-8
        content_type = resp.headers.get("Content-Type", "")
        charset = "utf-8"
        if "charset=" in content_type:
            charset = content_type.split("charset=")[-1].strip()
        html_bytes = resp.read()
        return html_bytes.decode(charset, errors="replace")


# ==================== 主入口 ====================
def main():
    """主流程：获取页面 -> 解析HTML -> 去重 -> 保存CSV。"""
    print(f"正在获取页面: {PAGE_URL}")
    html = fetch_page(PAGE_URL)
    print(f"页面获取成功，大小: {len(html)} 字节")

    print("正在解析方剂列表...")
    parser = FormulaParser()
    parser.feed(html)  # 将HTML内容喂给解析器，触发状态机运行

    print(f"共找到 {len(parser.formulas)} 个方剂条目")

    # 去重（保持顺序）—— 同一URL可能在页面不同位置出现多次，
    # 这里使用 seen 集合记录已出现的URL，保留首次出现的顺序
    seen = set()
    unique_formulas = []
    for name, url in parser.formulas:
        if url not in seen:
            seen.add(url)
            unique_formulas.append((name, url))

    print(f"去重后剩余 {len(unique_formulas)} 个方剂条目")

    # 保存为CSV，使用 utf-8-sig 编码（带BOM），确保在 Excel 中直接打开时中文不乱码
    csv_path = OUTPUT_CSV
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["方剂名称", "方剂名称的URL"])
        writer.writerows(unique_formulas)

    print(f"已保存到: {csv_path}")

    # 打印前10条作为预览
    print("\n--- 前10条预览 ---")
    for name, url in unique_formulas[:10]:
        print(f"  {name} -> {url}")
    if len(unique_formulas) > 10:
        print(f"  ... 共 {len(unique_formulas)} 条")


if __name__ == "__main__":
    main()
