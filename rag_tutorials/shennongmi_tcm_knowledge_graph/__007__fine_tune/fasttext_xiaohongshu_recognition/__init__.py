"""
fastText 小红书发布意图识别 子包
==================================

本包提供基于 fastText 的小红书发布意图二分类功能，
包含训练脚本和推理模块。

功能组成:
    - train_fasttext_intent.py: 训练脚本，使用 autotune 自动超参数搜索
    - fasttext_predictor.py:    推理模块，提供懒加载单例预测器

使用示例:
    # 训练模型（需先执行 generate_training_data.py 生成训练数据）
    python -m __007__fine_tune.fasttext_xiaohongshu_recognition.train_fasttext_intent

    # 推理调用
    from __007__fine_tune.fasttext_xiaohongshu_recognition.fasttext_predictor import (
        predict_xhs_intent,
    )
    is_publish, confidence = predict_xhs_intent("帮我写一篇小红书笔记")
"""

# fastText 小红书发布意图识别
# - train_fasttext_intent.py: 训练脚本
# - fasttext_predictor.py:    推理模块
