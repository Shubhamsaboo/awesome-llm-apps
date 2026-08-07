"""
意图识别训练数据 子包
=====================

本包包含训练数据生成脚本，用于为以下两个意图识别模型生成训练数据:

1. fastText 小红书发布意图识别
   - 输出: fasttext_xhs_train.txt / fasttext_xhs_val.txt
   - 格式: __label__发布/__label__非发布 + 空格分隔的分词文本
   - 目标: 2500 条（正负各 1250），自动 80/20 拆分为训练/验证集

2. RoBERTa + LoRA 中医意图识别
   - 输出: roberta_tcm_intent.csv
   - 格式: text,target（target 为 "是" 或 "否"）
   - 目标: 4000 条（正负各 2000）

数据生成方式:
    基于大量手工编写的模板和话题池，通过模板填充 + 前后缀随机组合
    的方式自动生成多样化训练样本。数据已经过去重和正负样本平衡处理。

使用方式:
    python -m __007__fine_tune.intent_recognition_data.generate_training_data

    # 或直接运行
    python generate_training_data.py

注意事项:
    - 运行前请确保已安装 jieba 分词库
    - 随机种子固定为 42，确保每次生成的数据一致（可复现）
    - 生成的数据文件保存在当前目录下
"""

# 意图识别训练数据
# - generate_training_data.py: 自动生成 fastText 和 RoBERTa 训练数据
