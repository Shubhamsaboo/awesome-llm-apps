"""
Chinese-RoBERTa-wwm-ext + LoRA 中医意图识别 子包
=================================================

本包提供基于 hfl/chinese-roberta-wwm-ext 预训练模型、
使用 LoRA（Low-Rank Adaptation，低秩适配）微调的中医意图
二分类功能，包含训练脚本和推理模块。

技术栈:
    - 基座模型:  hfl/chinese-roberta-wwm-ext（哈工大讯飞联合中文 RoBERTa）
    - 微调方法:  LoRA（冻结基座模型参数，仅训练低秩适配矩阵）
    - 分类任务:  二分类（是否为中医相关问题）

功能组成:
    - train_roberta_tcm_intent.py: 训练脚本，LoRA 微调 + 早停 + 混合精度
    - roberta_tcm_predictor.py:    推理模块，懒加载单例 + 线程安全锁

训练命令:
    # 从项目根目录运行
    python -m __007__fine_tune.chineserobertawwmext_zhongyi_recognition.train_roberta_tcm_intent

    # 或在包目录下直接运行
    python train_roberta_tcm_intent.py

推理使用:
    # 对外暴露的接口（通过 __init__.py 重导出）
    from __007__fine_tune.chineserobertawwmext_zhongyi_recognition import predict_tcm_intent
    is_zhongyi = predict_tcm_intent("枸杞有什么功效")  # True

    # 同时获取置信度
    from __007__fine_tune.chineserobertawwmext_zhongyi_recognition import predict_with_confidence
    is_zhongyi, conf = predict_with_confidence("今天天气怎么样")  # (False, 0.95)

模型输出目录:
    __007__fine_tune/model/roberta_tcm_intent_lora/
        - adapter_config.json       LoRA 适配器配置
        - adapter_model.safetensors LoRA 适配器权重
        - tokenizer 相关文件        分词器配置
"""

# 从推理模块重导出主要对外接口，简化调用方导入路径
from __007__fine_tune.chineserobertawwmext_zhongyi_recognition.roberta_tcm_predictor import (
    predict_tcm_intent,
    predict_with_confidence,
)

# __all__ 控制 from package import * 时导出的符号
__all__ = [
    "predict_tcm_intent",
    "predict_with_confidence",
]
