"""
fastText 小红书发布意图识别 —— 训练脚本
==========================================

功能概述:
    使用 fastText 内置的 autotune（自动超参数搜索）功能，
    基于验证集自动寻找最优超参数（学习率、epoch、词向量维度、
    N-gram 窗口等），训练二分类模型（发布意图 vs 非发布意图）。

    相比手动调参，autotune 可以在给定的时间/空间预算内自动
    探索超参数空间，节省大量试错时间。

数据格式要求（fastText 标准格式）:
    __label__发布 帮 我 写 一篇 小红书 笔记
    __label__非发布 感冒 了 吃什么 中药

    每行一条样本，标签前缀为 __label__，文本需预先使用
    jieba 分词并以空格分隔。训练数据由 generate_training_data.py
    自动生成。

训练流程:
    1. 检查训练/验证数据文件是否存在，统计标签分布
    2. 调用 train_supervised() + autotune 自动搜索超参数
    3. 在验证集上评估最终模型（精确率、召回率、F1）
    4. 保存模型到 __007__fine_tune/model/fasttext_xhs_intent.bin
    5. 用典型输入做手动测试，直观感受模型效果

用法:
    python train_fasttext_intent.py

    # 或作为模块运行
    python -m __007__fine_tune.fasttext_xiaohongshu_recognition.train_fasttext_intent

输出:
    - __007__fine_tune/model/fasttext_xhs_intent.bin  （训练好的 fastText 模型）

注意事项:
    - fastText 在 NumPy 2.x 环境下，Python 包装层的 model.predict()
      会因 np.array(probs, copy=False) 抛出 ValueError，本脚本
      使用 model.f.predict() 底层 C++ 绑定绕过该问题
    - autotuneModelSize 限制模型大小上限，避免内存溢出
"""

import fasttext
import os
import sys
import time

# 确保能导入项目内部模块（如 common.path_utils）
# 将项目根目录加入 sys.path（train_fasttext_intent.py 位于
# __007__fine_tune/fasttext_xiaohongshu_recognition/ 下，需上溯 3 级）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.path_utils import get_file_path


# ============================================================
# 路径配置
# ============================================================

# 训练/验证数据路径（由 generate_training_data.py 生成）
TRAIN_FILE = get_file_path("__007__fine_tune/intent_recognition_data/fasttext_xhs_train.txt")
VAL_FILE = get_file_path("__007__fine_tune/intent_recognition_data/fasttext_xhs_val.txt")

# 模型保存路径
MODEL_DIR = get_file_path("__007__fine_tune/model")
MODEL_PATH = os.path.join(MODEL_DIR, "fasttext_xhs_intent.bin")

# autotune 配置
AUTOTUNE_DURATION = 300  # 自动超参数搜索最大时长（秒），5 分钟
# autotune 模型大小上限，防止搜索出 GB 级别的巨型模型导致 OOM。
# 格式为 "XXM"（兆字节）或 "XXG"（千兆字节）
AUTOTUNE_MODEL_SIZE = "300M"


# ============================================================
# 工具函数
# ============================================================

def check_data(label: str, filepath: str):
    """
    检查数据文件是否存在，并统计标签分布。

    功能:
        1. 确认文件存在，否则抛出 FileNotFoundError
        2. 逐行解析 fastText 格式数据，统计各标签的样本数
        3. 打印标签分布信息（样本数 + 百分比）

    参数:
        label:    数据集的描述标签（如 "训练集"、"验证集"），仅用于日志输出
        filepath: 数据文件的完整路径

    返回:
        total: 有效样本总数（不含空行）
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"{label}文件不存在: {filepath}")

    # 统计各标签的样本数
    label_counts = {}
    total = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue  # 跳过空行
            total += 1
            # fastText 标签以 __label__ 开头，取每行第一个匹配的标签
            for token in line.split():
                if token.startswith("__label__"):
                    label_counts[token] = label_counts.get(token, 0) + 1
                    break  # 一条样本只需要一个标签

    # 打印标签分布
    print(f"\n📊 {label} ({filepath})")
    print(f"   总样本数: {total}")
    for lbl, cnt in sorted(label_counts.items()):
        print(f"   {lbl}: {cnt} ({100*cnt/total:.1f}%)")
    return total


def train_with_autotune():
    """
    使用 fastText autotune 自动搜索最优超参数并训练模型。

    训练原理:
        fastText 的 autotune 机制会在给定的时间预算内自动尝试
        不同的超参数组合（学习率、epoch、词向量维度 dim、
        wordNgrams 窗口大小等），在验证集上评估每组参数的效果，
        最终返回验证集上表现最好的模型。

        - autotuneValidationFile: 指定验证集路径，autotune 每轮
          搜索后用该数据评估模型
        - autotuneDuration: 整个搜索过程的时间上限（秒）
        - autotuneModelSize: 限制模型文件的磁盘大小上限，防止
          搜索到大 dim 值导致 GB 级模型、内存溢出

    返回:
        model: 训练好的 fastText 模型实例
    """
    print("\n" + "=" * 60)
    print("🚀 开始 fastText 训练（autotune 自动超参数搜索）")
    print("=" * 60)
    print(f"   训练集: {TRAIN_FILE}")
    print(f"   验证集: {VAL_FILE}")
    print(f"   最大搜索时长: {AUTOTUNE_DURATION} 秒")
    print(f"   模型大小上限: {AUTOTUNE_MODEL_SIZE}")
    print(f"   模型保存路径: {MODEL_PATH}")

    start_time = time.time()

    # —— autotune 训练 ——
    # train_supervised 是 fastText 的监督学习入口函数
    # 传入 autotuneValidationFile 即启用自动超参数搜索模式
    # verbose=2 打印详细训练日志（每轮 autotune 的尝试结果）
    model = fasttext.train_supervised(
        input=TRAIN_FILE,
        autotuneValidationFile=VAL_FILE,
        autotuneDuration=AUTOTUNE_DURATION,
        autotuneModelSize=AUTOTUNE_MODEL_SIZE,
        verbose=2,
    )

    elapsed = time.time() - start_time
    print(f"\n⏱️ 训练+超参数搜索总耗时: {elapsed:.1f} 秒")

    # —— 在验证集上评估最终模型 ——
    print("\n" + "=" * 60)
    print("📊 最终模型验证集评估")
    print("=" * 60)

    # model.test() 返回三元组: (样本数, precision@1, recall@1)
    # precision@1: 模型预测为类别 X 的样本中真正属于 X 的比例
    # recall@1:    真正属于 X 的样本中被正确预测的比例
    samples, precision, recall = model.test(VAL_FILE)
    # F1 分数是精确率和召回率的调和平均，综合衡量模型效果
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    print(f"   验证样本数: {samples}")
    print(f"   Precision:  {precision:.4f}  ({precision*100:.2f}%)")
    print(f"   Recall:     {recall:.4f}  ({recall*100:.2f}%)")
    print(f"   F1 Score:   {f1:.4f}  ({f1*100:.2f}%)")

    # —— 保存模型 ——
    os.makedirs(MODEL_DIR, exist_ok=True)  # 确保模型目录存在
    model.save_model(MODEL_PATH)
    model_size = os.path.getsize(MODEL_PATH)
    print(f"\n✅ 模型已保存: {MODEL_PATH}")
    print(f"   大小: {model_size / 1024:.1f} KB ({model_size / 1024 / 1024:.1f} MB)")

    # —— 打印训练出的超参数 ——
    print("\n" + "=" * 60)
    print("📋 模型信息")
    print("=" * 60)
    print(f"   词向量维度: {model.get_dimension()}")
    print(f"   标签数量: {len(model.labels)}")
    print(f"   标签列表: {model.labels}")

    return model


def test_manual_examples(model):
    """
    用几条典型输入做手动测试，直观感受模型效果。

    测试场景覆盖:
        - 明确的发布意图（"帮我写一篇小红书笔记..."）
        - 中医咨询（"感冒了吃什么中药"）
        - 日常闲聊（"你好，今天天气不错"）
        - 隐式发布意图（"我要分享..."）
        - 非中医/非发布问题（"劳动仲裁怎么申请"）

    注意:
        输入文本需使用 jieba 分词（与训练数据格式一致），
        否则模型可能无法正确理解文本。

    参数:
        model: 训练好的 fastText 模型实例
    """
    import jieba
    import numpy as np

    def _safe_predict(text, k=1):
        """
        NumPy 2.x 兼容的 predict 封装函数。

        问题背景:
            fastText Python 包装层的 model.predict() 内部会调用
            np.array(probs, copy=False)，在 NumPy 2.x 下会抛出
            ValueError（copy 参数行为变更）。

        解决方案:
            直接调用底层 C++ 绑定 model.f.predict()，该接口返回
            list[tuple[float, str]] 格式的 (概率, 标签) 列表，
            然后用 np.asarray() 重新包装概率值。

        注意:
            model.f.predict() 的签名和返回值格式与 model.predict() 不同：
              - 签名: (text, k, threshold, label_prefix)  — 全部是位置参数
              - 返回: list[tuple[float, str]]  — (概率, 标签) 元组列表
              - 第 4 参数 '' 表示不过滤任何标签前缀
        """
        raw = model.f.predict(text, k, 0.0, '')
        # 分别提取标签名和概率值
        labels = [item[1] for item in raw]  # item[1] 是标签字符串
        probs = np.asarray([item[0] for item in raw])  # item[0] 是概率浮点数
        return labels, probs

    # 测试用例：覆盖发布/非发布多种场景
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
    ]

    print("\n" + "=" * 60)
    print("🧪 手动测试示例")
    print("=" * 60)

    for text in test_cases:
        # 分词：将中文文本切分为空格分隔的词序列
        tokenized = " ".join(jieba.lcut(text))
        # 取 Top-1 预测结果
        labels, probs = _safe_predict(tokenized, k=1)
        label = labels[0]    # 预测的标签（__label__发布 或 __label__非发布）
        prob = probs[0]       # 该标签的置信度 (0~1)
        # 映射到可读标签名称
        readable = "发布" if label == "__label__发布" else "非发布"
        print(f"  [{readable}] (置信度: {prob:.4f}) | {text}")

    print("=" * 60)


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    # 1. 检查数据：确认训练集和验证集文件存在，并查看标签分布
    check_data("训练集", TRAIN_FILE)
    check_data("验证集", VAL_FILE)

    # 2. 训练模型：autotune 自动搜索最优超参数
    model = train_with_autotune()

    # 3. 手动测试：用典型样本直观验证模型效果
    test_manual_examples(model)

    print("\n🎉 训练完成！")
