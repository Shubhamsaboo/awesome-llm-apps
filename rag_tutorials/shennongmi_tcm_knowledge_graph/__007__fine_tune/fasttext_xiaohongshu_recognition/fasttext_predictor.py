"""
fastText 小红书发布意图识别 —— 推理模块
==========================================

功能概述:
    加载训练好的 fastText 二分类模型（.bin 格式），对外提供
    小红书发布意图预测接口。采用模块级懒加载单例模式，首次
    调用时自动加载模型，后续调用复用同一实例，避免重复加载开销。

核心设计:
    - 懒加载单例: 通过 get_predictor() 获取全局唯一预测器实例，
      首次调用时加载模型（可能耗时 1~3 秒），后续调用零开销
    - jieba 自动分词: 输入原始中文文本即可，内部自动完成分词，
      与训练数据格式保持一致
    - NumPy 2.x 兼容: 绕过 fastText Python 包装层在 NumPy 2.x 下
      的 np.array(copy=False) 兼容性问题，直接调用 C++ 绑定层
    - 阈值过滤: 支持自定义置信度阈值，低于阈值的"发布"预测
      按保守策略处理为"非发布"

用法示例:
    # 方式1: 直接调用快捷预测函数
    from __007__fine_tune.fasttext_xiaohongshu_recognition.fasttext_predictor import (
        predict_xhs_intent,
        get_predictor,
    )
    is_publish, confidence = predict_xhs_intent("帮我写一篇小红书笔记")

    # 方式2: 获取 predictor 实例，可复用
    predictor = get_predictor()
    is_publish, confidence = predictor.predict("帮我写一篇小红书笔记")
    label, conf = predictor.predict_label("感冒了吃什么中药")

注意事项:
    - 模型在首次调用时懒加载（非线程安全，多线程需自行加锁）
    - 如果模型文件不存在，会抛出 FileNotFoundError 并提示先运行训练脚本
    - 输入文本为空或仅含空白字符时，始终返回 (False, 0.0)
"""

import os
import sys
from typing import Tuple

import jieba

# 确保能导入项目内部模块（如 common.path_utils）
# 将项目根目录加入 sys.path（当前文件位于 __007__fine_tune/fasttext_xiaohongshu_recognition/ 下，
# 需上溯 3 级到达项目根目录）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.path_utils import get_file_path


# ============================================================
# 路径配置
# ============================================================

# fastText 训练好的模型文件路径
MODEL_PATH = get_file_path("__007__fine_tune/model/fasttext_xhs_intent.bin")


# ============================================================
# FastTextPredictor —— 预测器类
# ============================================================

class FastTextPredictor:
    """
    fastText 二分类预测器（小红书发布意图识别）。

    封装了模型加载、分词处理、预测逻辑和 NumPy 2.x 兼容处理，
    对外提供统一的 predict() 和 predict_label() 接口。

    设计要点:
        - 初始化时即加载模型（非懒加载），确保实例可用
        - 自动抑制 fastText 加载时的冗余警告输出
        - 所有文本输入自动经 jieba 分词处理

    Attributes:
        model:      fastText 模型实例（fasttext.FastText._FastText）
        model_path: 模型文件 (.bin) 的完整路径

    异常:
        FileNotFoundError: 模型文件不存在时立即抛出，而非延迟到首次预测
    """

    def __init__(self, model_path: str = MODEL_PATH):
        """
        初始化预测器，加载 fastText 模型文件。

        加载流程:
            1. 检查模型文件是否存在
            2. 导入 fasttext 库
            3. 抑制 fasttext.FastText.eprint 的警告输出
            4. 加载 .bin 模型文件到内存

        参数:
            model_path: fastText 模型文件 (.bin) 的完整路径

        异常:
            FileNotFoundError: 模型文件不存在，附带训练脚本的路径提示
        """
        self.model_path = model_path
        if not os.path.isfile(self.model_path):
            raise FileNotFoundError(
                f"fastText 模型文件不存在: {self.model_path}\n"
                f"请先运行训练脚本: python __007__fine_tune/fasttext_xiaohongshu_recognition/train_fasttext_intent.py"
            )

        import fasttext
        # 抑制 fastText 加载时的冗余警告输出（如 "Warning: ..." 等）
        # 将 eprint 替换为空操作，保持输出整洁
        fasttext.FastText.eprint = lambda *args, **kwargs: None
        self.model = fasttext.load_model(self.model_path)
        print(f"✅ fastText 模型已加载: {self.model_path}")

    def predict(self, text: str, threshold: float = 0.85) -> Tuple[bool, float]:
        """
        预测用户输入是否具有小红书发布意图。

        预测流程:
            1. 检查输入文本是否为空（空文本直接返回非发布）
            2. 使用 jieba 分词，输出空格分隔的词序列
            3. 调用底层 C++ 绑定进行预测
            4. 根据标签和置信度阈值判断最终结果
                - 标签为 "__label__发布" 且置信度 >= threshold → True
                - 否则 → False（保守策略：宁可漏判也不误判）

        参数:
            text:      用户原始输入文本（中文，无需预先分词）
            threshold: 置信度阈值（0.0 ~ 1.0），仅当预测为"发布"且
                       置信度 >= threshold 时才返回 True。
                       设为 0.0 则完全信任模型预测的标签。

        返回:
            (is_publish_intent, confidence):
                - is_publish_intent: bool，True 表示具有发布意图
                - confidence: float (0.0 ~ 1.0)，模型对预测标签的置信度
        """
        # 空文本处理：空字符串或仅含空白字符的输入直接返回非发布
        if not text or not text.strip():
            return False, 0.0

        # 分词：使用 jieba 精确模式切分中文文本
        # 输出格式与训练数据一致（空格分隔的词序列）
        tokenized = " ".join(jieba.lcut(text.strip()))

        # 调用底层 C++ 绑定方法预测，避免 NumPy 2.x 兼容问题
        # _raw_predict 内部使用 model.f.predict() 代替 model.predict()
        # k=1 表示只取 Top-1 预测结果
        labels, probs = self._raw_predict(tokenized, k=1)

        predicted_label = labels[0]  # 预测的标签（__label__发布 或 __label__非发布）
        confidence = probs[0]         # 该标签的置信度 (0~1)

        # 阈值过滤逻辑
        if predicted_label == "__label__发布":
            if confidence >= threshold:
                # 高置信度"发布"预测 → 判定为发布意图
                return True, confidence
            else:
                # 预测为"发布"但置信度不足 → 保守按"非发布"处理
                # 避免低置信度的误判干扰下游逻辑
                return False, confidence
        else:
            # 预测为"非发布" → 直接返回非发布
            return False, confidence

    def predict_label(self, text: str) -> Tuple[str, float]:
        """
        预测并返回原始标签名和置信度（不做 threshold 过滤）。

        与 predict() 的区别:
            - predict() 做了阈值判断，返回 bool
            - predict_label() 返回原始标签字符串，不做任何过滤
            - 适用于需要查看原始预测结果的调试/分析场景

        参数:
            text: 用户原始输入文本（中文）

        返回:
            (label, confidence):
                - label:      字符串，"__label__发布" 或 "__label__非发布"
                - confidence: 浮点数，模型对标签的置信度 (0.0 ~ 1.0)
        """
        # 空文本直接返回非发布
        if not text or not text.strip():
            return "__label__非发布", 0.0

        # 分词 + 预测
        tokenized = " ".join(jieba.lcut(text.strip()))
        labels, probs = self._raw_predict(tokenized, k=1)
        return labels[0], probs[0]

    def _raw_predict(self, text: str, k: int = 1):
        """
        NumPy 2.x 兼容的底层预测调用。

        问题背景:
            fastText Python 包装层的 model.predict() 方法内部使用了
            `np.array(probs, copy=False)`，在 NumPy 2.x 中 copy 参数
            行为发生了变更，会导致 ValueError。

        解决方案:
            直接调用 C++ 绑定层的 model.f.predict() 方法，它在底层
            返回 list[tuple[float, str]] 格式的结果，不涉及 NumPy
            的 copy 参数问题。然后用 np.asarray() 重新包装概率数组。

        注意:
            model.f.predict() 的签名与 model.predict() 不同：
              - 签名: (text, k, threshold, label_prefix)
              - 第 4 参数: 标签前缀过滤器，传 '' 表示不过滤任何标签。
                之前误传 'strict' 导致所有标签被过滤（无标签以
                'strict' 开头），返回空结果，现已修复。
              - 返回: list[tuple[float, str]] — (概率, 标签) 元组列表

        参数:
            text: 已分词的中文文本（空格分隔的词序列）
            k:    取 Top-k 个预测结果

        返回:
            (labels, probs):
                - labels: list[str]，预测的标签列表
                - probs:  numpy.ndarray，对应的概率数组
        """
        import numpy as np
        # 第 4 参数 '' 表示不过滤标签前缀，返回所有可能的标签
        raw = self.model.f.predict(text, k, 0.0, '')
        # item[1] 是标签字符串（如 "__label__发布"），item[0] 是概率值
        labels = [item[1] for item in raw]
        probs = np.asarray([item[0] for item in raw])
        return labels, probs


# ============================================================
# 模块级单例（懒加载）
# ============================================================

# 全局预测器实例，初始为 None，首次调用时初始化
_predictor: FastTextPredictor = None


def get_predictor() -> FastTextPredictor:
    """
    获取全局单例 FastTextPredictor 实例。

    采用懒加载模式:
        - 首次调用: 初始化 FastTextPredictor()，加载 .bin 模型文件
          （可能需要 1~3 秒，取决于模型大小和磁盘 IO）
        - 后续调用: 直接返回已缓存的实例，零额外开销

    线程安全说明:
        本函数非线程安全。在多线程环境下，首次并发调用可能导致
        模型被重复加载。如需多线程使用，请在调用方自行加锁，或
        在应用启动时预先调用一次 get_predictor() 完成初始化。

    返回:
        FastTextPredictor: 全局唯一的预测器实例
    """
    global _predictor
    if _predictor is None:
        _predictor = FastTextPredictor()
    return _predictor


def predict_xhs_intent(text: str, threshold: float = 0.85) -> Tuple[bool, float]:
    """
    快捷预测函数：判断用户输入是否具有小红书发布意图。

    这是最常用的对外接口，内部调用全局单例预测器。

    参数:
        text:      用户原始输入文本（中文）
        threshold: 置信度阈值（0.0 ~ 1.0），默认 0.85。
                   阈值越高越严格（宁可不判发布也不误判）
                   阈值越低越宽松（宁可误判也不漏判）

    返回:
        (is_publish_intent, confidence):
            - is_publish_intent: bool，True 表示具有发布意图
            - confidence: float，模型的置信度（0.0 ~ 1.0）

    示例:
        >>> predict_xhs_intent("帮我写一篇小红书笔记")
        (True, 0.95)

        >>> predict_xhs_intent("感冒了吃什么中药")
        (False, 0.92)
    """
    return get_predictor().predict(text, threshold=threshold)


# ============================================================
# 测试代码（直接运行此文件时执行）
# ============================================================

if __name__ == "__main__":
    # 测试用例：(文本, 预期标签)
    # 预期标签: True=发布意图, False=非发布意图
    test_cases = [
        "帮我写一篇小红书笔记，分享枸杞养生茶的做法",
        "感冒了吃什么中药",
        "你好，今天天气不错",
        "我要发小红书，内容是艾灸养生",
        "四君子汤由哪些药材组成",
        "帮我写个朋友圈文案",
        "帮我写一篇小红书种草笔记介绍花胶鸡汤",
        "什么星座最配",
        "写一篇科普帖发小红书上",
        "劳动仲裁怎么申请",
        "帮我写一篇养生分享",  # 隐式发布意图（无"小红书"关键词）
        "最近失眠严重中医有什么办法",  # 症状咨询，非发布意图
    ]

    print("=" * 60)
    print("🧪 fastText 小红书意图预测测试")
    print("=" * 60)

    predictor = get_predictor()

    correct = 0
    total = 0
    # 每个测试用例对应的预期标签（True=发布, False=非发布）
    expected = [True, False, False, True, False, False, True, False, True, False, True, False]

    for text, exp in zip(test_cases, expected):
        # 使用默认阈值 0.85 进行预测
        is_publish, conf = predictor.predict(text)
        label_str = "发布" if is_publish else "非发布"
        # 同时获取原始标签，方便对比分析
        raw_label, raw_conf = predictor.predict_label(text)
        status = "✅" if is_publish == exp else "❌"
        print(f"  {status} [{label_str}] conf={conf:.4f} | raw={raw_label}({raw_conf:.4f}) | {text}")
        if is_publish == exp:
            correct += 1
        total += 1

    print(f"\n  准确率: {correct}/{total} = {100*correct/total:.1f}%")
    print("=" * 60)
