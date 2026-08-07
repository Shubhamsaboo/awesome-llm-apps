"""
方剂知识图谱提取脚本

从爬取的方剂文本文件中提取结构化的中医知识图谱数据。
该脚本调用 extract_from_folder 函数，对 "方剂" 文件夹内的所有 .txt 文件进行批量处理，
将提取的实体和关系保存为 JSON 文件，同时生成可用于 LLM 微调的训练数据集。

输入：__001__clawler/方剂/ 目录下的 .txt 文件（爬虫采集的方剂文本）
输出：
    - extract_formula_data.json: 知识图谱提取结果（包含实体和关系）
    - extract_formula_finetune_data.json: 微调格式数据（instruction-input-output 三元组）

注：方剂文本通常包含方剂的组成药材、功效主治、用法禁忌等信息，
    LLM 会从中提取方剂、药材、疾病、症状、功效等实体及它们之间的关系。
"""
from __002__extract_information.__000__extract_graph_data_utils import extract_from_folder
from common.path_utils import get_file_path

# 调用批量提取函数
# 参数说明：
#   第1个参数：文本源文件夹（爬虫数据中的方剂目录）
#   第2个参数：知识图谱结果保存路径
#   第3个参数：微调训练数据保存路径
extract_from_folder(get_file_path("__001__clawler/方剂"),
                    get_file_path("__002__extract_information/extract_formula_data.json"),
                    get_file_path("__002__extract_information/extract_formula_finetune_data.json"))