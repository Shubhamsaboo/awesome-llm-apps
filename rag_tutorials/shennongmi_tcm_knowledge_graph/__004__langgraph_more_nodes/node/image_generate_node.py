"""
AI 图片生成节点（火山引擎即梦 AI）
=====================================

角色定位:
    LangGraph 小红书发布链路的配图生成节点。位于 text_generate_node 之后，
    根据已生成的标题和正文，调用火山引擎即梦 AI (Jimeng AI) 生成
    符合中医养生主题风格的配图。

核心功能:
    1. 根据标题和正文内容构建图片生成 prompt（中医养生风格）
    2. 调用火山引擎 VisualService SDK 进行文生图 (Text-to-Image)
    3. 下载生成的图片到本地 picture/ 目录
    4. 将图片路径写入 AgentState

完整流程:
    标题 + 正文
      → sanitize_title_for_filename() → 生成安全文件名
      → generate_jimeng_prompt()       → 构建文生图 prompt
      → generate_image()               → 调用即梦 AI API
        → download_image_from_url()    → 下载图片到本地
      → 图片路径写入 state["xiaohongshu_image_path_list"]

依赖:
    - volcengine.visual.VisualService: 火山引擎视觉服务 SDK
    - common.config.Config: 统一配置管理（含 JIMENG_AK / JIMENG_SK）
    - 火山引擎即梦 AI API (jimeng_t2i_v40)

注意事项:
    - 需要在 Config 中配置有效的火山引擎 AK/SK
    - 生成图片有 API 调用成本（按量计费）
    - 图片生成失败时不会中断工作流，错误详情写入 xiaohongshu_tcm_tip
"""

import os
import requests

import datetime

from volcengine.visual.VisualService import VisualService
from __004__langgraph_more_nodes.agent_state import AgentState
from common.config import Config
from common.path_utils import get_file_path

conf = Config()


def sanitize_title_for_filename(title: str, max_length: int = 10) -> str:
    """
    将标题字符串清洗成适合作为文件名的格式。

    处理步骤:
      1. 去除文件名中的非法字符 (\\ / : * ? " < > |)
      2. 去除换行符和制表符
      3. 截取前 max_length 个字符（避免文件名过长）
      4. 前缀添加时间戳以保证唯一性

    参数:
        title (str): 原始标题文本
        max_length (int): 标题部分截取的最大字符数，默认 10

    返回:
        str: 清洗后的文件名，格式为 YYYYMMDDHHmmss + 截取标题 + .png
             例如: "20260729143025枸杞泡水养.png"

    用途:
        确保生成的图片文件名不包含操作系统不允许的字符，
        避免因文件名非法导致图片保存失败。
    """
    # 定义操作系统文件名中的非法字符集合（Windows + Unix）
    illegal_chars = r'\/:*?"<>|'
    # 使用 str.translate 高效移除所有非法字符（映射为 None → 删除）
    cleaned_title = title.translate(str.maketrans("", "", illegal_chars))
    # 去除换行和制表符（这些虽然不是非法字符，但会影响文件名可读性）
    cleaned_title = cleaned_title.replace("\n", "").replace("\r", "").replace("\t", "")
    # 截取前 max_length 个字符，避免文件名过长（部分文件系统有路径长度限制）
    truncated_title = cleaned_title[:max_length]
    # 获取当前时间戳，确保文件名唯一（防止同名覆盖）
    now = datetime.datetime.now()
    time_str = now.strftime("%Y%m%d%H%M%S")
    return time_str + truncated_title + ".png"


def generate_jimeng_prompt(title: str, content: str) -> str:
    """
    根据小红书标题和正文构建即梦 AI 文生图 prompt。

    策略:
      用中文详细描述画面场景、氛围、色调和内容要求，
      引导 AI 生成符合中医养生主题风格的高质量配图。

    关键要求:
      - 画面内容与标题主题相关
      - 可包含养生行为场景（冥想、泡脚、煮药、食疗、经络按摩等）
      - 整体氛围温和、宁静、有疗愈感
      - 色调自然柔和
      - 图片中不能有任何文字（避免影响美感）

    参数:
        title (str): 小红书帖子标题
        content (str): 小红书帖子正文（截取前 100 字作为参考）

    返回:
        str: 即梦 AI 文生图 prompt 文本
    """
    # 截取 content 前 100 字作为图像生成的上下文参考
    # 控制 prompt 长度，避免超出 API 限制
    content_snippet = content[:100] if content else ""
    return (
        f"一幅围绕中医养生主题创作的图像，画面展现与标题内容相关的场景，"
        f"构图中包含人物或物品与养生行为（如冥想、泡脚、煮药、食疗、经络按摩等），"
        f"整体氛围温和、宁静、有疗愈感，色调自然柔和，背景可融入自然或居家环境，"
        f"表达健康、平衡与舒缓的情绪。"
        f"图片内容主题为:{title}。"
        f"参考正文内容:{content_snippet}。"
        f"图片中不能有任何文字。"
        f"整体画面和谐、美观，符合图片质量要求。"
        f"图片中包含与中医养生主题相关的元素，如中药、穴位、食物、运动等。"
        f"文字与画面协调，不影响整体美感。允许画风自由表达，可现代、写意、插画、水彩或其他形式。"
    )


def download_image_from_url(url: str, output_path: str):
    """
    从 URL 下载图片并保存到本地文件。

    使用流式下载 (stream=True)，分块读取数据，避免将大图片
    一次性加载到内存中导致内存溢出。

    参数:
        url (str): 图片的 HTTP/HTTPS 下载地址（由即梦 AI API 返回）
        output_path (str): 图片本地保存路径（绝对路径）

    异常:
        RuntimeError: 下载失败时抛出，包含原始异常信息
    """
    try:
        # 流式 GET 请求，避免大文件一次性加载到内存
        response = requests.get(url, stream=True)
        # 如果 HTTP 状态码非 2xx，抛出 HTTPError
        response.raise_for_status()
        # 分块写入文件（每块 8KB），适合大图片下载
        with open(output_path, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)
        print(f"图片已保存：{output_path}")
    except requests.exceptions.RequestException as e:
        print(f"下载失败：{e}")
        raise RuntimeError(f"图片下载失败: {e}") from e


def generate_image(prompt: str, output_path: str):
    """
    调用火山引擎即梦 AI 文生图 API 生成图片。

    使用火山引擎 VisualService SDK 调用即梦 t2i v4.0 模型:
      - req_key: "jimeng_t2i_v40"（即梦文生图 v4.0）
      - return_url: True（要求 API 返回临时下载 URL）

    参数:
        prompt (str): 文生图 prompt 文本
        output_path (str): 图片本地保存路径

    返回:
        str: 图片本地保存路径（与 output_path 相同）

    异常:
        RuntimeError: 图像生成失败或无有效图片链接返回时抛出
    """
    # 初始化火山引擎视觉服务客户端
    visual_service = VisualService()
    # 设置 API 访问密钥 (Access Key) 和秘密密钥 (Secret Key)
    visual_service.set_ak(conf.JIMENG_AK)
    visual_service.set_sk(conf.JIMENG_SK)

    # 构建 API 请求参数
    form = {
        "req_key": "jimeng_t2i_v40",   # 即梦文生图 v4.0 模型
        "prompt": prompt,               # 图片生成提示词
        "return_url": True              # 要求返回临时图片 URL（而非 base64）
    }

    # 调用火山引擎视觉处理服务
    resp = visual_service.cv_process(form)
    # 从响应中提取图片 URL 列表
    image_urls = resp.get('data', {}).get('image_urls', [])
    if image_urls:
        # 目前只取第一张生成的图片
        download_image_from_url(image_urls[0], output_path)
        return output_path
    else:
        raise RuntimeError("图像生成失败，无有效图片链接返回")


def xiaohongshu_image_generator(title, content):
    """
    小红书配图生成的编排函数。

    串联 prompt 生成 → API 调用 → 图片下载的完整流程。

    参数:
        title (str): 小红书帖子标题
        content (str): 小红书帖子正文

    返回:
        str: 生成的图片本地保存路径
    """
    # 步骤1: 根据标题和正文生成即梦 AI prompt
    prompt = generate_jimeng_prompt(title, content)

    # 步骤2: 确保图片输出目录存在
    os.makedirs(get_file_path("picture"), exist_ok=True)
    # 步骤3: 生成安全的文件名（时间戳 + 标题截取）
    file_name = sanitize_title_for_filename(title)
    output_path = os.path.join(get_file_path("picture"), file_name)

    # 步骤4: 调用即梦 AI 生成图片
    image_path = generate_image(prompt, output_path)
    return image_path


def image_generator_node(state: AgentState):
    """
    根据标题和内容生成中医养生风格的小红书配图（LangGraph 节点）。

    从 AgentState 读取 xiaohongshu_tcm_post_title 和
    xiaohongshu_tcm_post_content，调用即梦 AI 生成配图，
    并将图片路径写入 xiaohongshu_image_path_list。

    参数:
        state (AgentState): LangGraph 全局状态，包含:
            - xiaohongshu_tcm_post_title: 帖子标题
            - xiaohongshu_tcm_post_content: 帖子正文

    返回:
        AgentState: 更新后的状态，新增/修改字段:
            - xiaohongshu_image_path_list: [图片路径列表]
            - xiaohongshu_tcm_tip: 生成结果提示信息

    容错设计:
        图片生成过程中的任何异常都会被捕获，不会中断 LangGraph 工作流。
        - 成功: xiaohongshu_image_path_list 包含图片路径
        - 失败: xiaohongshu_image_path_list 为空，错误详情写入 xiaohongshu_tcm_tip
          下游 check_text_image_node 会检测到图片缺失并阻止发布
    """
    try:
        print("开始生成小红书图片生成")
        title = state.get('xiaohongshu_tcm_post_title')
        content = state.get('xiaohongshu_tcm_post_content')

        # 调用图片生成编排函数
        image_path = xiaohongshu_image_generator(title, content)

        # 将图片路径存入状态（列表形式，支持多图扩展）
        state['xiaohongshu_image_path_list'] = [image_path]
        print(f"图片生成成功: {image_path}")
        state['xiaohongshu_tcm_tip'] = "图片生成成功"
        print("完成生成小红书图片生成")
        return state
    except Exception as e:
        # 打印完整异常堆栈，便于排查 API 调用问题
        import traceback
        traceback.print_exc()
        err_detail = f"图片生成失败: {str(e)}"
        state['xiaohongshu_image_path_list'] = []
        # 🔧 修复：将详细错误写入 tip，下游 check_text_image_node 会检测并传播真实原因
        state['xiaohongshu_tcm_tip'] = err_detail
        print(err_detail)
        return state


if __name__ == '__main__':
    # 构建测试用的 AgentState（模拟完整的状态字典）
    test_state: AgentState = {
        "input": "生成小红书文案, 吃荔枝相关",
        "is_xiaohongshu_publish_intent": True,
        "xiaohongshu_tcm_post_title": "吃荔枝有什么好处呢？姐妹们！",
        "xiaohongshu_tcm_post_content": "很多好处",
        "xiaohongshu_image_path_list": [],
        "xiaohongshu_tcm_tip": "",
        "is_can_publish_xiaohongshu": False,
        "xiaohongshu_markdown_output": "",
        "is_zhongyi_intent": False,
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
        "is_all_validate_cypher": False,
        "cypher_validation_feedback": "",
        "cypher_retry_count": 0,
        "cypher_results": [],
        "neo4j_answer": "",
        "output": "",
    }
    image_generator_node(state=test_state)
