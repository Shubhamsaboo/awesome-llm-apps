"""
HTML/Markdown 结果展示页面生成节点
=======================================

角色定位:
    LangGraph 小红书发布链路的收尾节点。无论发布成功还是失败，
    本节点都会生成一个 HTML 页面来展示完整的发布结果，
    包括标题、正文、配图和发布状态。

核心功能:
    1. 将本地图片路径转换为 HTTP URL（通过本地文件服务器访问）
    2. 根据发布状态生成对应的状态提示（成功/失败 + 原因）
    3. 拼接完整的 HTML 页面（含 CSS 样式、Flexbox 图片画廊）
    4. 将生成的 HTML 写入 AgentState，供前端渲染展示

数据流向:
    AgentState (title, content, image_paths, is_can_publish, tip)
      → generate_markdown_node
      → xiaohongshu_markdown_output (完整 HTML 页面)
      → output (同步到最终输出)

依赖:
    - common.path_utils: 项目根目录和路径工具
    - AgentState: LangGraph 全局状态
"""

import os

from __004__langgraph_more_nodes.agent_state import AgentState
from common.path_utils import root_dir, get_file_path


def trans_image_path_list(image_path_list: list):
    """
    将本地图片绝对路径列表转换为可通过 HTTP 访问的 URL 列表。

    原理:
      项目通过 FastAPI 挂载了静态文件服务，本地文件的相对路径
      可通过 http://localhost:8000/{relative_path} 访问。
      本函数将每个绝对路径转为相对于项目根目录的路径，
      然后拼接为完整的 HTTP URL。

    参数:
        image_path_list (list): 本地图片绝对路径列表

    返回:
        list: HTTP URL 列表，例如 ["http://localhost:8000/picture/xxx.png", ...]
    """
    def trans_image_path(image_path):
        # 计算图片路径相对于项目根目录的相对路径
        relative_path = os.path.relpath(image_path, root_dir)
        # 拼接为本地文件服务器的 HTTP URL
        return f"http://localhost:8000/{relative_path}"

    return [trans_image_path(image_path) for image_path in image_path_list]


def generate_markdown_code(title, content, image_path_list, image_width="300px", image_height="300px",
                          publish_success=True, tip=""):
    """
    生成展示小红书发布结果的完整 HTML 页面。

    页面结构:
      - 发布状态（成功 ✅ / 失败 ❌ + 失败原因）
      - 帖子标题
      - 帖子正文
      - 图片画廊（Flexbox 横向排列，支持自动换行）

    参数:
        title (str): 帖子标题
        content (str): 帖子正文
        image_path_list (list): 本地图片路径列表（将被转为 HTTP URL）
        image_width (str): 图片显示宽度，默认 "300px"
        image_height (str): 图片显示高度，默认 "300px"
        publish_success (bool): 发布是否成功，默认 True
        tip (str): 发布失败时的提示信息（仅在 publish_success=False 时显示）

    返回:
        str: 完整的 HTML 页面字符串
    """
    # 将本地路径转换为可被浏览器访问的 HTTP URL
    image_path_list = trans_image_path_list(image_path_list)

    # 🔧 修复：根据实际发布状态显示不同结果提示
    # 成功: "✅ 小红书发布成功"
    # 失败: "❌ 小红书发布失败（原因）"
    if publish_success:
        status_text = f"<p>✅ 小红书发布成功</p>"
    else:
        status_text = f"<p>❌ 小红书发布失败（{tip or '未知原因'}）</p>"

    # 构建 HTML 页面结构
    # 使用简单的内联样式，不依赖外部 CSS 文件
    html_code = f"""
    <html>
        <head>
            <title>{title}</title>
            <style>
                /* Flexbox 图片画廊: 横向排列，自动换行，10px 间距 */
                .image-container {{
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                    justify-content: flex-start;
                }}
                /* 图片统一尺寸，使用 object-fit 保持比例 */
                .image-container img {{
                    width: {image_width};
                    height: {image_height};
                }}
            </style>
        </head>
        <body>
            {status_text}
            <h3>标题：{title}</h3>
            <p>内容：{content}</p>
            <div class="image-container">
    """

    # 为每张图片生成 <img> 标签
    for image_path in image_path_list:
        html_code += f'<img src="{image_path}" alt="image"/>\n'

    # 关闭未闭合的 HTML 标签
    html_code += """</div>
        </body>
    </html>
    """

    return html_code


def generate_markdown_node(state: AgentState):
    """
    根据标题和内容生成展示发布结果的 HTML 页面（LangGraph 节点）。

    这是小红书发布链路的最后一步，无论发布成功与否都会执行。
    生成的 HTML 包含完整的发布信息，供用户查看和确认。

    参数:
        state (AgentState): LangGraph 全局状态，包含:
            - xiaohongshu_tcm_post_title: 帖子标题
            - xiaohongshu_tcm_post_content: 帖子正文
            - xiaohongshu_image_path_list: 图片路径列表
            - is_can_publish_xiaohongshu: 发布是否成功
            - xiaohongshu_tcm_tip: 发布结果提示信息

    返回:
        AgentState: 更新后的状态，新增/修改字段:
            - xiaohongshu_markdown_output: 完整 HTML 页面字符串
            - output: 同步到最终输出字段（供前端直接展示）
    """
    title = state.get('xiaohongshu_tcm_post_title') or ""
    content = state.get('xiaohongshu_tcm_post_content') or ""
    image_path_list = state.get('xiaohongshu_image_path_list') or []

    # 🔧 修复：根据实际发布结果显示不同状态文字，而非始终硬编码"发布成功"
    is_success = state.get('is_can_publish_xiaohongshu', False)
    tip = state.get('xiaohongshu_tcm_tip', '')

    # 生成完整的 HTML 页面
    markdown = generate_markdown_code(title, content, image_path_list,
                                      publish_success=is_success, tip=tip)

    # 将 HTML 写入状态，供前端渲染
    state['xiaohongshu_markdown_output'] = markdown
    state['output'] = markdown
    return state


if __name__ == '__main__':
    # 测试: 生成包含两张测试图片的 HTML 页面并打印
    print(generate_markdown_code("标题", "内容",
                                 [get_file_path("picture/1.png"),
                                  get_file_path("picture/2.png")]))
