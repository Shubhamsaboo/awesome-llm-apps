"""
Neo4j 图数据库元数据导出脚本

将 Neo4j 图数据库中的 Schema 元数据（包括节点标签、关系类型、
属性键及其类型等）导出为 JSON 文件，供下游应用（如前端展示、
知识图谱可视化、数据文档生成等）使用。

输出文件：
    tcm_metadata.json: 保存在当前脚本所在目录（__003__create_neo4j_database/）
    内容包含：
        - node_labels: 所有节点标签及其属性定义
        - relationship_types: 所有关系类型及其属性定义
"""
import os

from common.neo4j_manager import neo4j_client

# 将JSON结果保存到当前脚本所在目录（即 __003__create_neo4j_database/）
output_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(output_dir, "tcm_metadata.json")

# 调用 neo4j_client 的元数据导出方法
# export_tcm_metadata_to_json 会查询 Neo4j 的 Schema 信息，
# 包括节点标签列表、关系类型列表、各标签/类型的属性键与类型，
# 并序列化为 JSON 文件写入磁盘
neo4j_client.export_tcm_metadata_to_json(output_path)
