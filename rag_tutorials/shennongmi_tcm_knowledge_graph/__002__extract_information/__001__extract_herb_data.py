"""
药材知识图谱提取脚本

从爬取的药材文本文件中提取结构化的中医知识图谱数据。
该脚本调用 extract_from_folder 函数，对 "中药" 文件夹内的所有 .txt 文件进行批量处理，
将提取的实体和关系保存为 JSON 文件，同时生成可用于 LLM 微调的训练数据集。

输入：__001__clawler/中药/ 目录下的 .txt 文件（爬虫采集的药材文本）
输出：
    - extract_herb_data.json: 知识图谱提取结果（包含实体和关系）
    - extract_herb_finetune_data.json: 微调格式数据（instruction-input-output 三元组）
"""
from __002__extract_information.__000__extract_graph_data_utils import extract_from_folder
from common.path_utils import get_file_path

# 调用批量提取函数
# 参数说明：
#   第1个参数：文本源文件夹（爬虫数据中的中药目录）
#   第2个参数：知识图谱结果保存路径
#   第3个参数：微调训练数据保存路径
extract_from_folder(get_file_path("__001__clawler/中药"),
                    get_file_path("__002__extract_information/extract_herb_data.json"),
                    get_file_path("__002__extract_information/extract_herb_finetune_data.json"))