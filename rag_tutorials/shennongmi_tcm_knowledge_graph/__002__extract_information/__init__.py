"""
__002__extract_information 包

本包负责从中医文本数据中提取结构化知识图谱信息，包括实体（Entity）和关系（Relation）。
通过调用大语言模型（LLM），从爬取的药材和方剂文本中抽取症状、疾病、方剂、药材、功效、出处等实体，
以及它们之间的治疗、缓解、包含、具有等关系。

主要模块：
    - __000__extract_graph_data_utils: 知识图谱抽取的核心工具（Pydantic 数据模型、异步批量处理）
    - __001__extract_herb_data: 从爬取的药材文本中提取知识图谱
    - __002__extract_formula_data: 从爬取的方剂文本中提取知识图谱
"""
# extract_information package
