"""
LangGraph 工作流图可视化工具
============================

提供将 LangGraph 编译后的状态图（CompiledStateGraph）导出为 PNG 图片的功能，
便于开发阶段的可视化调试和文档生成。

主要功能:
    - output_pic_graph(): 将 LangGraph 工作流图渲染为 Mermaid PNG 图片并保存到磁盘

技术原理:
    LangGraph 的 get_graph().draw_mermaid_png() 方法内部:
        1. 将状态图转换为 Mermaid 流程图 DSL（Domain Specific Language）
        2. 调用 Mermaid Ink API (https://mermaid.ink/) 将 DSL 渲染为 PNG 图片
        3. 返回 PNG 图片的二进制数据
    因此调用此函数需要网络连接（访问 Mermaid Ink 服务）。

典型用法:
    from common.output_graph_utils import output_pic_graph

    # 在构建完 LangGraph workflow 后导出可视化图
    app = workflow.compile()
    output_pic_graph(app, "my_workflow.png")

注意事项:
    - 需要网络连接才能访问 Mermaid Ink API 渲染图片
    - 如果 Mermaid Ink 服务不可用，会打印异常信息但不会中断程序
"""

from langgraph.graph.state import CompiledStateGraph


def output_pic_graph(app: CompiledStateGraph, filename: str = "graph.png"):
    """
    将 LangGraph 编译后的工作流图导出为 PNG 图片文件。

    此函数调用 LangGraph 内置的 Mermaid 图表生成功能，将状态图（节点和边）
    以可视化的流程图形式保存为 PNG 图片。适用于开发阶段的调试、文档编写
    和架构展示。

    Args:
        app (CompiledStateGraph): LangGraph 编译后的状态图实例。
                                  通过 workflow.compile() 获取。
        filename (str): 输出 PNG 文件的路径。默认为 "graph.png"，
                        保存在当前工作目录。建议使用绝对路径或
                        项目根目录下的相对路径。

    Returns:
        None: 结果直接写入文件系统。

    Raises:
        此函数不向外抛出异常。所有异常在内部捕获并打印到 stdout，
        确保可视化失败不会中断主程序的运行。

    Example:
        >>> from langgraph.graph import StateGraph
        >>> workflow = StateGraph(MyState)
        >>> # ... 添加节点和边 ...
        >>> app = workflow.compile()
        >>> output_pic_graph(app, "outputs/my_agent_graph.png")

    Side Effects:
        在 filename 指定路径创建 PNG 图片文件。如果文件已存在则被覆盖。
        调用 Mermaid Ink API（https://mermaid.ink/）进行渲染，需要网络连接。
    """
    try:
        # get_graph() 返回底层的 Graph 对象
        # draw_mermaid_png() 内部将图转为 Mermaid DSL 再调用 Mermaid Ink API 渲染，
        # 返回值为 PNG 图片的二进制数据
        png_data = app.get_graph().draw_mermaid_png()
        # 以二进制写入模式保存 PNG 图片
        with open(filename, 'wb') as f:
            f.write(png_data)
    except Exception as e:
        # 可视化失败不应中断主流程，仅打印错误信息
        # 常见失败原因：网络不通、Mermaid Ink 服务不可用、graph 结构异常
        print(f"导出 LangGraph 工作流图失败: {e}")
