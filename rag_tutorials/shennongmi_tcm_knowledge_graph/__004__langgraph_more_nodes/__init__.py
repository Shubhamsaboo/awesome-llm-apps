"""
__004__langgraph_more_nodes 包

基于 LangGraph 构建的中医智能体工作流包，集成了三条核心业务链路：

  1. 小红书中医养生内容自动发布链路
     用户输入发布意图 → 生成文案 → 生成配图 → 内容完整性校验 → 自动发布 → 输出 Markdown 结果

  2. 中医知识图谱问答链路
     用户输入中医问题 → 实体抽取 → FAISS 向量匹配 → Cypher 生成与校验 → Neo4j 查询 → 自然语言回答

  3. 非中医兜底链路
     用户输入与中医无关 → LLM 直接回答

包结构概览：
  - agent_state.py           —— 工作流状态定义（AgentState TypedDict）及初始状态工厂函数
  - langgraph_more_nodes.py  —— 主工作流定义（build_workflow 构建状态图）、路由函数、集成测试
  - node/                    —— 各节点实现模块（意图识别、实体抽取、Cypher 生成等）

使用方式：
  >>> from __004__langgraph_more_nodes.langgraph_more_nodes import run_workflow, zhongyi_response
  >>> result = run_workflow("枸杞有什么功效？")
  >>> print(result["output"])
"""
