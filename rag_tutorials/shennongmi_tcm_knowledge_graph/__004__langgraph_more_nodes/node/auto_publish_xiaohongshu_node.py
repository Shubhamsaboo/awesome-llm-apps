"""
小红书自动发布节点（Playwright 浏览器自动化）
==================================================

角色定位:
    LangGraph 小红书发布链路的最终节点。位于 check_text_image_node 之后，
    使用 Playwright 启动 Chromium 浏览器，自动将 AgentState 中的标题、
    正文和图片发布到小红书创作者平台。

核心功能:
    1. 启动持久化 Chromium 浏览器（保持 cookie 登录状态）
    2. 检测是否需要登录并等待手动扫码
    3. 通过多种策略上传图片、填写标题、填写正文
    4. 通过坐标点击方式触发发布按钮

技术选型理由:
    小红书创作者平台是复杂的 SPA (单页应用)，没有公开 API，
    因此采用浏览器自动化方案。选择 Playwright (而非 Selenium):
      - 更快的启动速度
      - 更好的自动等待机制
      - 持久化浏览器上下文 (launch_persistent_context) 保留 cookie

发布流程:
    1. 启动 Chrome → 导航到创作者发布页
    2. 登录检测 → 未登录则等待手动扫码（120s 超时）
    3. 上传图片（3 种策略依次尝试）
    4. 填写标题（3 种策略依次尝试）
    5. 填写正文（3 种策略依次尝试）
    6. 坐标/JS 定位点击发布按钮（3 种方案依次尝试）
    7. 处理可能的二次确认弹窗

多策略容错设计:
    由于小红书创作者平台的前端代码经常更新（DOM 结构调整、类名哈希化），
    每个操作步骤都设计了 2-3 种备选策略，依次尝试直到成功。
    降低因平台 UI 小改版导致的自动化失败概率。

发布地址:
    https://creator.xiaohongshu.com/publish/publish?from=homepage&target=image&source=official

依赖:
    - playwright>=1.40.0 (sync_api)
    - 首次运行前需要: playwright install chromium
    - 首次发布需要手动扫码登录（cookie 持久化到 cookie/browser_data/）

页面布局参考（小红书创作者平台 - 图文发布页）:
    ┌──────────────────────────────────────────────────┐
    │  发布笔记                              [发布]     │  ← 顶栏
    ├──────────────┬───────────────────────────────────┤
    │              │   标题 [_______________] 0/20     │
    │  图片上传区  │                                   │
    │  (虚线框)    │   正文 [_______________________]  │
    │              │                                   │
    │  支持jpg...   │   #话题  @朋友  📍位置            │
    ├──────────────┴───────────────────────────────────┤
    │              [暂存离开]    [发布]                │  ← 底部按钮栏
    └──────────────────────────────────────────────────┘

注意事项:
    - headless=False 是必需的（小红书有反自动化检测）
    - 坐标点击策略依赖 viewport 尺寸，不同屏幕可能需要微调
    - 登录超时 120 秒，超时后自动返回失败状态
"""

import os
import sys
import time
from typing import List

from playwright.sync_api import sync_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeout

# 确保能导入项目内部模块（方便直接运行脚本测试）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.path_utils import get_file_path
from __004__langgraph_more_nodes.agent_state import AgentState

# ============================================================
# 配置常量
# ============================================================

# 小红书创作者平台图文发布页 URL
PUBLISH_URL = (
    "https://creator.xiaohongshu.com/publish/publish"
    "?from=homepage&target=image&source=official"
)
# 持久化浏览器数据目录（保存 cookie、localStorage 等，免重复登录）
BROWSER_DATA_DIR = get_file_path("cookie/browser_data")
# 通用等待超时 30 秒（页面加载、元素出现等）
DEFAULT_TIMEOUT = 30_000
# 登录等待超时 120 秒（留给用户充沛的扫码时间）
LOGIN_TIMEOUT = 120_000

# ============================================================
# 工具函数
# ============================================================


def _resolve_image_paths(image_paths: List[str]) -> List[str]:
    """
    将图片路径解析为绝对路径，过滤不存在的文件。

    由于 AgentState 中存储的图片路径可能是相对路径，
    需要先转换为绝对路径，并验证文件是否真实存在，
    避免 Playwright 上传失败。

    参数:
        image_paths: 图片路径列表（可能是相对路径或绝对路径）

    返回:
        list: 验证后的绝对路径列表
    """
    valid = []
    for p in (image_paths or []):
        if not p:
            continue
        # 如果已经是绝对路径则直接使用，否则基于项目目录拼接
        abs_path = p if os.path.isabs(p) else get_file_path(p)
        if os.path.isfile(abs_path):
            valid.append(abs_path)
        else:
            print(f"⚠️ 图片不存在已跳过: {abs_path}")
    return valid


def _check_need_login(page: Page) -> bool:
    """
    检测当前页面是否被重定向到登录页。

    小红书未登录用户访问发布页时会被重定向到登录页，
    需要检测以下特征:
      - URL 包含 'login'
      - 页面出现 '手机号登录' 文案
      - 页面出现 '扫码登录' 文案

    参数:
        page: Playwright Page 对象

    返回:
        bool: True 表示需要登录，False 表示已登录
    """
    if "login" in page.url.lower():
        return True
    try:
        page.wait_for_selector('text=手机号登录', timeout=3000)
        return True
    except PlaywrightTimeout:
        pass
    try:
        page.wait_for_selector('text=扫码登录', timeout=2000)
        return True
    except PlaywrightTimeout:
        pass
    return False


def _wait_page_stable(page: Page, extra_sleep: float = 2.0):
    """
    等待 SPA 页面完全加载（网络空闲 + 额外渲染时间）。

    小红书是典型的 SPA (Single Page Application)，页面初始化后
    还有异步 API 请求和 DOM 渲染。networkidle 状态表示网络请求
    已基本完成，extra_sleep 留出额外的 JS 渲染时间。

    参数:
        page: Playwright Page 对象
        extra_sleep: networkidle 后的额外等待秒数，默认 2 秒
    """
    try:
        page.wait_for_load_state('networkidle', timeout=15_000)
    except PlaywrightTimeout:
        pass  # 超时不中断，继续进行
    time.sleep(extra_sleep)


# ============================================================
# Step 1: 上传图片
# ============================================================

def _upload_images(page: Page, image_paths: List[str]):
    """
    上传图片到小红书创作者平台的上传区域。

    采用三层策略依次尝试，提高成功率:
      策略A: 直接对隐藏的 input[type="file"] 设值 → 最可靠（绕过 UI 交互）
      策略B: 点击「上传图片」按钮触发文件选择器 → 模拟用户点击
      策略C: 点击页面左侧上传区域坐标触发文件选择器 → 暴力坐标法

    上传完成后等待「上传中」状态消失，确保文件传输完毕。

    参数:
        page: Playwright Page 对象
        image_paths: 已解析的绝对图片路径列表

    异常:
        RuntimeError: 所有上传方式均失败时抛出
    """
    print(f"\n📷 上传 {len(image_paths)} 张图片...")

    # —— 策略A: 直接对隐藏 file input 设值 ——
    # 小红书的上传组件通常包含隐藏的 <input type="file"> 元素
    # 直接对其 set_input_files() 不依赖 UI 交互，最可靠
    file_inputs = page.locator('input[type="file"]')
    count = file_inputs.count()
    print(f"  找到 {count} 个 file input")
    for i in range(count):
        try:
            file_inputs.nth(i).set_input_files(image_paths)
            print(f"  ✅ file input[{i}] 上传成功")
            time.sleep(3)  # 等待上传开始
            _wait_upload_done(page)
            return
        except Exception as e:
            print(f"  file input[{i}]: {e}")

    # —— 策略B: 点击「上传图片」按钮触发文件选择器 ——
    # 依次尝试多个可能的点击目标（文案可能是"上传图片"、"上传"等）
    print("  尝试点击上传按钮触发文件选择器...")
    click_targets = [
        page.locator('text=上传图片').first,
        page.locator('button:has-text("上传")').first,
        page.locator('text=上传').first,
    ]
    for target in click_targets:
        try:
            if target.count() > 0 and target.is_visible():
                # expect_file_chooser 监听文件对话框弹出事件
                with page.expect_file_chooser(timeout=5000) as fc:
                    target.click()
                fc.value.set_files(image_paths)
                print(f"  ✅ 通过文件选择器上传成功")
                time.sleep(3)
                _wait_upload_done(page)
                return
        except Exception:
            continue

    # —— 策略C: 点击页面左侧上传区域（坐标法） ——
    # 如果无法定位具体元素，用坐标点击上传区域的最常见位置
    # 图片上传区通常位于页面左侧 25% 宽度、35% 高度位置
    print("  尝试点击上传区域...")
    viewport = page.viewport_size
    if viewport:
        try:
            with page.expect_file_chooser(timeout=5000) as fc:
                page.mouse.click(viewport['width'] * 0.25, viewport['height'] * 0.35)
            fc.value.set_files(image_paths)
            print(f"  ✅ 坐标点击上传成功")
            time.sleep(3)
            _wait_upload_done(page)
            return
        except Exception as e:
            print(f"  坐标点击失败: {e}")

    raise RuntimeError("❌ 所有上传方式均失败")


def _wait_upload_done(page: Page, timeout: int = 60):
    """
    轮询检测图片上传是否完成。

    通过 JavaScript 检测页面文本中是否包含「上传中」或「uploading」字样，
    一旦消失即视为上传完成。最长等待 timeout 秒，超时后继续执行。

    参数:
        page: Playwright Page 对象
        timeout: 最大等待秒数，默认 60 秒
    """
    print("  ⏳ 等待上传完成...")
    for _ in range(timeout):
        # 通过 injected JS 检查页面中是否有"上传中"状态的文字
        uploading = page.evaluate("""() => {
            return document.body.innerText.includes('上传中') ||
                   document.body.innerText.includes('uploading');
        }""")
        if not uploading:
            print("  ✅ 上传完成")
            return
        time.sleep(1)
    print("  ⚠️ 上传等待超时")


# ============================================================
# Step 2: 填写标题
# ============================================================

def _fill_title(page: Page, title: str):
    """
    填写帖子标题到小红书发布页的标题输入框。

    采用三层策略依次尝试:
      策略1: 通过 placeholder="标题" 定位 input → 最精确
      策略2: 通过 JS 查找「标题」文本标签附近的 input → 语义定位
      策略3: 找页面上半部分最宽的可见 input → 启发式定位

    参数:
        page: Playwright Page 对象
        title: 帖子标题文本

    异常:
        RuntimeError: 所有定位方式均失败时抛出
    """
    print(f"\n✏️ 填写标题: {title}")

    # —— 策略1: 通过 placeholder 属性含"标题"定位 ——
    el = page.locator('input[placeholder*="标题"]').first
    if el.count() > 0:
        el.wait_for(state="visible", timeout=DEFAULT_TIMEOUT)
        el.click(); el.fill(""); el.type(title, delay=50)
        print("✅ 标题填写完成（placeholder）")
        return

    # —— 策略2: JS 遍历 DOM，找到文本为「标题」的标签，在其父链上找 input ——
    # 小红书的标签栏可能用纯文本标签而非 <label> 元素
    found = page.evaluate("""() => {
        const walker = document.createTreeWalker(
            document.body, NodeFilter.SHOW_TEXT, null, false);
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.trim() === '标题') {
                let p = node.parentElement;
                for (let i = 0; i < 5; i++) {
                    if (!p) break;
                    // 跳过 file 和 hidden 类型的 input
                    const inp = p.querySelector('input:not([type="file"]):not([type="hidden"])');
                    if (inp && inp.offsetParent) { inp.focus(); inp.select(); return true; }
                    p = p.parentElement;
                }
            }
        }
        return false;
    }""")
    if found:
        page.keyboard.type(title, delay=50)
        print("✅ 标题填写完成（JS定位）")
        return

    # —— 策略3: 启发式 —— 找页面上半部分最宽的可见 input ——
    # 在发布页面中，标题输入框通常是最宽的那个输入框
    found = page.evaluate("""() => {
        const inputs = document.querySelectorAll('input:not([type="file"]):not([type="hidden"])');
        let best = null, bestW = 0;
        for (const inp of inputs) {
            if (!inp.offsetParent) continue;
            const r = inp.getBoundingClientRect();
            if (r.top < window.innerHeight * 0.5 && r.width > bestW) { best = inp; bestW = r.width; }
        }
        if (best) { best.focus(); best.select(); return true; }
        return false;
    }""")
    if found:
        page.keyboard.type(title, delay=50)
        print("✅ 标题填写完成（最大宽度input）")
        return

    raise RuntimeError("❌ 找不到标题输入框")


# ============================================================
# Step 3: 填写正文
# ============================================================

def _fill_content(page: Page, content: str):
    """
    填写帖子正文到小红书发布页的正文编辑区。

    小红书使用 contenteditable div 作为富文本编辑器（而非 <textarea>），
    需要通过 keyboard.insert_text() 模拟打字输入。

    采用三层策略依次尝试:
      策略1: 遍历所有 contenteditable="true" 元素，用可见的最大那个
      策略2: 遍历所有 <textarea> 元素（如果改版后使用）
      策略3: JS 查找「正文」文本标签附近的编辑器

    参数:
        page: Playwright Page 对象
        content: 帖子正文文本

    异常:
        RuntimeError: 所有定位方式均失败时抛出
    """
    print(f"✏️ 填写正文（{len(content)} 字）...")

    # —— 策略1: 遍历所有 contenteditable，用可见且面积最大的那个 ——
    # 小红书的正文编辑器是 contenteditable="true" 的 div
    editors = page.locator('[contenteditable="true"]')
    cnt = editors.count()
    print(f"  找到 {cnt} 个 contenteditable")
    for i in range(cnt):
        ed = editors.nth(i)
        try:
            if not ed.is_visible():
                continue
            ed.click(); time.sleep(0.3)
            ed.fill(""); time.sleep(0.2)
            # 使用 keyboard.insert_text 模拟逐字输入（contenteditable 不支持 fill）
            ed.page.keyboard.insert_text(content)
            print(f"✅ 正文填写完成（contenteditable[{i}]）")
            return
        except Exception as e:
            print(f"  contenteditable[{i}]: {e}")

    # —— 策略2: 遍历所有 textarea 元素 ——
    # 如果小红书改版后使用 textarea 作为编辑区域
    textareas = page.locator('textarea')
    for i in range(textareas.count()):
        ta = textareas.nth(i)
        try:
            if ta.is_visible():
                ta.fill(content)
                print(f"✅ 正文填写完成（textarea[{i}]）")
                return
        except Exception as e:
            print(f"  textarea[{i}]: {e}")

    # —— 策略3: JS 查找「正文」文本标签附近的编辑器 ——
    # TreeWalker 遍历所有文本节点，找到"正文"标签后在父链上找编辑器
    found = page.evaluate("""() => {
        const all = document.querySelectorAll('*');
        for (const el of all) {
            if (el.innerText && el.innerText.trim() === '正文' && el.children.length <= 2) {
                let p = el.parentElement;
                for (let i = 0; i < 5; i++) {
                    if (!p) break;
                    const ed = p.querySelector('[contenteditable="true"], textarea, [role="textbox"]');
                    if (ed && ed.offsetParent) { ed.focus(); ed.click(); return true; }
                    p = p.parentElement;
                }
            }
        }
        return false;
    }""")
    if found:
        page.keyboard.insert_text(content)
        print("✅ 正文填写完成（JS定位正文标签）")
        return

    raise RuntimeError("❌ 找不到正文编辑区")


# ============================================================
# Step 4: 点击发布（坐标暴力法 + JS 定位）
# ============================================================

def _click_publish(page: Page):
    """
    点击发布按钮，触发笔记发布。

    背景:
      小红书底部按钮栏使用自定义元素 <xhs-publish-btn>，类名哈希化，
      传统 CSS 选择器匹配极不稳定。因此采用多方案组合:
        - 方案1: 定位 xhs-publish-btn 自定义元素，基于其 bounding_box 计算坐标
        - 方案2: JS 遍历底部所有 button，找文本含「发布」且在页面下半部分的
        - 方案3: 暴力坐标 —— 页面底部偏右固定坐标

    小红书底部按钮栏结构（参考截图）:
      - 容器标签: <xhs-publish-btn> 或类似自定义元素
      - 两个按钮: [暂存离开] 在左侧, [发布] 在右侧, gap 约 24px
      - 容器高度约 90px, 发布按钮约 120px 宽, 40px 高, 居中排列
      - 发布按钮中心约在容器宽度的 65% 位置

    点击后调用 _confirm_if_needed 处理可能的二次确认弹窗。
    """
    print("\n🚀 点击发布按钮（坐标暴力法）...")
    time.sleep(2)  # 等待内容完全渲染

    viewport = page.viewport_size
    vw = viewport['width']
    vh = viewport['height']

    # —— 方案1: 找 xhs-publish-btn 自定义元素，基于其 bounding_box 计算坐标 ——
    # 利用小红书自定义元素的名称为突破口，通过几何计算定位发布按钮
    try:
        container = page.locator('xhs-publish-btn').first
        if container.count() > 0:
            box = container.bounding_box()
            if box:
                # 发布按钮在容器内靠右，约 65% 位置，垂直居中
                btn_x = box['x'] + box['width'] * 0.65
                btn_y = box['y'] + box['height'] / 2
                print(f"  通过 xhs-publish-btn 定位: box=({box['x']:.0f},{box['y']:.0f},{box['width']:.0f},{box['height']:.0f})")
                print(f"  点击坐标: ({btn_x:.0f}, {btn_y:.0f})")
                page.mouse.click(btn_x, btn_y)
                time.sleep(2)
                _confirm_if_needed(page)
                print("✅ 发布按钮已点击（xhs-publish-btn 坐标）")
                return
    except Exception as e:
        print(f"  xhs-publish-btn 方案失败: {e}")

    # —— 方案2: 查找底部容器中所有 button，点最右边那个文本含「发布」的 ——
    # 通过 injected JS 遍历 button 的 getBoundingClientRect 来定位
    try:
        result = page.evaluate("""() => {
            // 找页面底部区域内的所有 button
            const buttons = document.querySelectorAll('button');
            let best = null, bestBottom = 0;
            for (const btn of buttons) {
                const text = (btn.innerText || '').trim();
                if (text === '发布' && btn.offsetParent) {
                    const rect = btn.getBoundingClientRect();
                    // 只考虑页面下半部分的按钮（底部按钮栏区域）
                    if (rect.bottom > window.innerHeight * 0.7) {
                        if (rect.bottom > bestBottom) {
                            best = btn;
                            bestBottom = rect.bottom;
                        }
                    }
                }
            }
            if (best) {
                const r = best.getBoundingClientRect();
                return {x: r.x + r.width / 2, y: r.y + r.height / 2, found: true};
            }
            return {found: false};
        }""")
        if result.get('found'):
            print(f"  JS 定位底部发布按钮, 坐标: ({result['x']:.0f}, {result['y']:.0f})")
            page.mouse.click(result['x'], result['y'])
            time.sleep(2)
            _confirm_if_needed(page)
            print("✅ 发布按钮已点击（JS 底部定位）")
            return
    except Exception as e:
        print(f"  JS 底部定位失败: {e}")

    # —— 方案3: 暴力坐标 —— 页面底部偏右区域 ——
    # 底部按钮栏大约在页面底部 90px 范围内
    # 发布按钮在右侧约 72% 宽度位置
    # 这是最后的兜底方案，坐标可能因页面缩放而偏移
    print(f"  使用暴力坐标: 页面右下角区域")
    btn_x = vw * 0.72   # 右侧 72% 宽度位置
    btn_y = vh - 45     # 距底部 45px（90px 高度容器的垂直中心）
    print(f"  点击坐标: ({btn_x:.0f}, {btn_y:.0f})")
    page.mouse.click(btn_x, btn_y)
    time.sleep(2)
    _confirm_if_needed(page)
    print("✅ 发布按钮已点击（暴力坐标）")


def _confirm_if_needed(page: Page):
    """
    处理发布后的二次确认弹窗。

    小红书在点击发布后有时会弹出确认对话框，
    包含「确定」或「确认」按钮。如果出现则自动点击确认。

    参数:
        page: Playwright Page 对象
    """
    try:
        page.wait_for_selector(
            'button:has-text("确定"), button:has-text("确认")',
            timeout=5000
        )
        page.locator('button:has-text("确定"), button:has-text("确认")').first.click()
        print("✅ 已确认发布")
    except PlaywrightTimeout:
        pass  # 无需二次确认，正常情况


# ============================================================
# 主节点函数
# ============================================================

def auto_publish_xiaohongshu_node(state: AgentState) -> AgentState:
    """
    小红书自动发布节点（LangGraph 节点）。

    这是小红书发布链路的最终节点，使用 Playwright 自动化操作浏览器，
    将 AgentState 中的标题、正文和图片发布到小红书创作者平台。

    参数:
        state (AgentState): LangGraph 全局状态，读取:
            - xiaohongshu_tcm_post_title:   笔记标题
            - xiaohongshu_tcm_post_content: 笔记正文
            - xiaohongshu_image_path_list:  图片路径列表

    返回:
        AgentState: 更新后的状态，写入:
            - is_can_publish_xiaohongshu: True/False（是否发布成功）
            - xiaohongshu_tcm_tip:        结果提示信息

    流程:
        1. 前置校验（标题、正文非空）
        2. 解析并验证图片路径
        3. 启动持久化 Chromium 浏览器（保留 cookie）
        4. 打开小红书创作者发布页面
        5. 检测登录状态，未登录则等待手动扫码（120s 超时）
        6. 上传图片 → 填写标题 → 填写正文
        7. 通过多种策略点击发布按钮
        8. 处理可能的二次确认弹窗
        9. 返回发布结果
    """
    title = state.get('xiaohongshu_tcm_post_title', '').strip()
    content = state.get('xiaohongshu_tcm_post_content', '').strip()
    image_paths = state.get('xiaohongshu_image_path_list', [])

    # —— 前置校验 ——
    if not title:
        state['is_can_publish_xiaohongshu'] = False
        state['xiaohongshu_tcm_tip'] = "发布失败：标题为空"
        print("❌ 标题为空")
        return state
    if not content:
        state['is_can_publish_xiaohongshu'] = False
        state['xiaohongshu_tcm_tip'] = "发布失败：正文为空"
        print("❌ 正文为空")
        return state

    # 解析并验证图片路径（过滤不存在的文件）
    resolved_images = _resolve_image_paths(image_paths)

    print("=" * 60)
    print(f"📝 自动发布小红书")
    print(f"   标题: {title}")
    print(f"   正文: {len(content)} 字")
    print(f"   图片: {len(resolved_images)} 张")
    print("=" * 60)

    try:
        # 启动 Playwright 同步 API
        with sync_playwright() as p:
            # 确保浏览器数据目录存在
            os.makedirs(BROWSER_DATA_DIR, exist_ok=True)

            # 使用持久化浏览器上下文:
            #   - 保存 cookie、localStorage 等数据到 BROWSER_DATA_DIR
            #   - 登录一次后下次运行无需重复扫码
            #   - headless=False: 必须显示浏览器窗口（小红书有反无头检测）
            context: BrowserContext = p.chromium.launch_persistent_context(
                user_data_dir=BROWSER_DATA_DIR,
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',  # 隐藏自动化特征
                    '--no-sandbox',  # Docker/CI 环境可能需要
                ],
                ignore_https_errors=True,
            )

            # 创建新页面并设置默认超时
            page: Page = context.new_page()
            page.set_default_timeout(DEFAULT_TIMEOUT)

            # ——— 步骤1: 打开发布页面 ———
            print("\n📍 打开发布页面...")
            page.goto(PUBLISH_URL, wait_until='domcontentloaded', timeout=DEFAULT_TIMEOUT)
            _wait_page_stable(page)

            # ——— 步骤2: 登录检测与等待 ———
            # 如果检测到登录页面，提示用户在浏览器中扫码
            # 等待 URL 跳转到发布页面即为登录成功
            if _check_need_login(page):
                print("\n⚠️ 需要登录，请在浏览器中扫码（120s超时）...")
                try:
                    page.wait_for_url("**/publish/publish**", timeout=LOGIN_TIMEOUT)
                    print("✅ 登录成功")
                    # 登录成功后重新导航到发布页面
                    page.goto(PUBLISH_URL, wait_until='domcontentloaded')
                    _wait_page_stable(page)
                except PlaywrightTimeout:
                    # 登录超时，将失败状态写入 state 并返回
                    state['is_can_publish_xiaohongshu'] = False
                    state['xiaohongshu_tcm_tip'] = "发布失败：登录超时"
                    context.close()
                    return state

            # ——— 步骤3: 上传图片 ———
            if resolved_images:
                _upload_images(page, resolved_images)
                _wait_page_stable(page)
            else:
                print("⚠️ 无图片上传")

            # ——— 步骤4: 填写标题 ———
            _fill_title(page, title)

            # ——— 步骤5: 填写正文 ———
            _fill_content(page, content)

            # ——— 步骤6: 点击发布按钮 ———
            print("\n⏳ 等待内容渲染...")
            time.sleep(3)  # 确保表单内容完全渲染后再点击
            _click_publish(page)

            # ——— 步骤7: 等待发布结果 ———
            print("⏳ 等待发布结果...")
            time.sleep(3)  # 等待服务器响应

            # 发布流程完成，设置成功状态
            state['is_can_publish_xiaohongshu'] = True
            state['xiaohongshu_tcm_tip'] = "发布成功"
            print("\n🎉 小红书发布流程完成！")
            context.close()

    except Exception as e:
        # 捕获所有异常，防止工作流因浏览器自动化异常而中断
        import traceback
        traceback.print_exc()
        state['is_can_publish_xiaohongshu'] = False
        state['xiaohongshu_tcm_tip'] = f"发布失败: {str(e)}"
        print(f"\n❌ 异常: {e}")

    return state


# ============================================================
# 测试代码
# ============================================================

if __name__ == '__main__':
    """
    测试入口。运行方式:
      python __004__langgraph_more_nodes/node/auto_publish_xiaohongshu_node.py

    注意事项:
      1. 首次运行需在浏览器中手动扫码登录（cookie 持久化后无需重复）
      2. 请在 picture/ 目录下放置测试图片
      3. 确保已执行: playwright install chromium
    """

    # ---- 准备测试图片 ----
    picture_dir = get_file_path("picture")
    test_images = []
    if os.path.isdir(picture_dir):
        for f in sorted(os.listdir(picture_dir)):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                test_images.append(os.path.join(picture_dir, f))

    if not test_images:
        print("⚠️  picture/ 目录下未找到图片，请先放入测试图片 (.png/.jpg)")

    # ---- 构造测试 AgentState ----
    test_state: AgentState = {
        "input": "我要发一篇关于枸杞养生的小红书",
        "is_xiaohongshu_publish_intent": True,
        "xiaohongshu_tcm_post_title": "枸杞泡水喝，这3个好处你知道吗？",
        "xiaohongshu_tcm_post_content": (
            "今天来给大家分享一个超简单的中医养生小知识～\n\n"
            "枸杞，大家都不陌生吧？\n"
            "但是你真的会吃枸杞吗？\n\n"
            "🍵 枸杞泡水的3大好处：\n\n"
            "1️⃣ 养肝明目\n"
            "枸杞入肝经，能滋补肝血。\n"
            "每天对着电脑的姐妹们，坚持喝枸杞水，眼睛会舒服很多！\n\n"
            "2️⃣ 补肾益精\n"
            "枸杞甘平，归肾经。\n"
            "经常熬夜、腰酸的朋友，可以试试枸杞泡水～\n\n"
            "3️⃣ 延缓衰老\n"
            "枸杞富含枸杞多糖和抗氧化成分，\n"
            "是天然的「抗老食材」！\n\n"
            "⚠️ 小贴士：\n"
            "• 每天10-15粒即可，不要贪多\n"
            "• 用60°C温水冲泡，不要用沸水\n"
            "• 上火期间暂时不要吃哦\n\n"
            "#中医养生 #枸杞 #养生日常 #中医小知识 #打工人养生"
        ),
        "xiaohongshu_image_path_list": test_images,
        "xiaohongshu_tcm_tip": "",
        "is_can_publish_xiaohongshu": False,
        "xiaohongshu_markdown_output": "",
        "is_zhongyi_intent": True,
        "direct_out": "",
        "user_input_effects": [],
        "user_input_diseases": [],
        "user_input_symptoms": [],
        "user_input_formulas": [],
        "user_input_herbs": [],
        "user_input_sources": [],
        "matched_effects": [],
        "matched_diseases": [],
        "matched_symptoms": [],
        "matched_formulas": [],
        "matched_herbs": [],
        "matched_sources": [],
        "cypher_query": [],
        "is_all_validate_cypher": True,
        "cypher_validation_feedback": "",
        "cypher_retry_count": 0,
        "cypher_results": [],
        "neo4j_answer": "",
        "output": "",
        "_stream_tokens": [],
        "messages": [],
    }

    print("\n" + "🧪" * 30)
    print("🧪 小红书自动发布 - 单元测试")
    print("🧪" * 30 + "\n")

    result_state = auto_publish_xiaohongshu_node(test_state)

    print("\n" + "=" * 60)
    print("📊 发布结果")
    print("=" * 60)
    print(f"  状态: {'✅ 成功' if result_state['is_can_publish_xiaohongshu'] else '❌ 失败'}")
    print(f"  提示: {result_state['xiaohongshu_tcm_tip']}")
    print(f"  标题: {result_state['xiaohongshu_tcm_post_title']}")
    print("=" * 60)
