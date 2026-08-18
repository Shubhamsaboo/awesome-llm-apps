"""
Chinese-RoBERTa-wwm-ext + LoRA 中医意图识别 —— 推理模块
=========================================================

功能概述:
    加载训练好的 LoRA 适配器权重，结合基座模型 hfl/chinese-roberta-wwm-ext，
    提供中医意图二分类（是否为中医相关问题）的推理接口。

核心设计:
    - **懒加载单例模式**: 首次调用 predict_tcm_intent() 时自动加载模型，
      后续调用复用同一实例，避免重复加载的开销（首次 ~2-5 秒，后续 ~0.01 秒）
    - **线程安全**: 使用 threading.Lock 保护模型加载过程，防止多线程并发
      首次调用导致模型被重复加载
    - **双重检查锁定**: 加锁后再检查 _loaded 标志，避免锁竞争时的重复加载
    - **自动设备检测**: 按 CUDA > MPS > CPU 优先级选择推理设备
    - **LoRA 合并优化**: CUDA 设备上自动调用 merge_and_unload() 将 LoRA
      权重合并到基座模型，消除适配器层的前向开销；非 CUDA 设备跳过合并
      （避免 macOS MPS/CPU 上的 segfault 风险）

对外接口:
    - predict_tcm_intent(text, threshold=0.5) -> bool
    - predict_with_confidence(text) -> (bool, float)

用法:
    from langgraph_workflow.tcm_predictor import (
        predict_tcm_intent,
        predict_with_confidence,
    )

    is_zhongyi = predict_tcm_intent("枸杞有什么功效")         # True
    is_zhongyi = predict_tcm_intent("今天天气不错")           # False
    is_zhongyi, confidence = predict_with_confidence("黄芪泡水")  # (True, 0.95)

注意事项:
    - 模型首次加载需从磁盘读取 LoRA 权重 + 从 HuggingFace（或缓存）加载
      基座模型，首次调用需等待数秒
    - 如果 LoRA 模型目录不存在或关键文件缺失，抛出 RuntimeError
    - 空文本或空白字符输入直接返回非中医
    - merge_and_unload 在 macOS 上跳过（稳定优先）
"""

import os
import sys
import threading
import warnings
from typing import Tuple

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from peft import PeftModel  # 用于加载和注入 LoRA 适配器

# 确保能导入项目内部模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.path_utils import get_file_path

warnings.filterwarnings("ignore")

# ============================================================
# 路径配置
# ============================================================

# LoRA 适配器权重保存目录（由 train_roberta_tcm_intent.py 训练产出）
LORA_MODEL_DIR = get_file_path("langgraph_workflow/model/roberta_tcm_intent_lora")

# 基座模型名称（需与训练时完全一致）
BASE_MODEL_NAME = "hfl/chinese-roberta-wwm-ext"

# ============================================================
# 推理超参数
# ============================================================

MAX_LENGTH = 128                              # 最大输入序列长度（与训练时一致）
                                              # 超过此长度的文本会被截断，不足则填充
CONFIDENCE_THRESHOLD = 0.5                     # 默认二分类阈值
                                              # 概率 > 0.5 判为「是（中医）」，否则判为「否」

# ============================================================
# 模型单例 —— 状态变量
# ============================================================

_model = None           # PeftModel 实例（或 merge_and_unload 后的完整模型）
_tokenizer = None       # AutoTokenizer 实例（中文 WordPiece 分词器）
_device = None          # 推理设备标识符（"cuda"/"mps"/"cpu"）
_lock = threading.Lock() # 线程安全锁，保护模型加载过程
_loaded = False         # 是否已尝试加载模型（无论成功与否），防止重复加载
_load_error = None      # 加载失败时的异常信息（供后续调用抛出清晰的错误）


# ============================================================
# 内部辅助函数
# ============================================================

def _get_device() -> str:
    """
    检测可用的推理设备，按优先级选择。

    检测顺序:
        1. CUDA（NVIDIA GPU）—— 推理性能最优
        2. MPS（Apple Silicon GPU on macOS）—— 需验证实际可用
        3. CPU —— 兜底方案，最慢但最稳定

    注意:
        MPS 在某些 PyTorch 版本上可能注册了后端但实际不可用，
        这里通过尝试创建张量并移动到 MPS 来验证。

    返回:
        str: 设备标识符（"cuda", "mps", 或 "cpu"）
    """
    if torch.cuda.is_available():
        return "cuda"
    # macOS 上 MPS (Apple Silicon GPU) 可用于推理加速
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        try:
            # 实际验证 MPS 是否可用（创建张量并移动到 MPS 设备）
            _ = torch.zeros(1).to("mps")
            return "mps"
        except Exception:
            pass  # MPS 不可用，回退到 CPU
    return "cpu"


def _load_model():
    """
    加载 LoRA 微调后的中医意图识别模型（仅在首次调用时执行一次）。

    加载流程:
        1. 获取互斥锁（确保多线程安全）
        2. 双重检查：获锁后再次检查 _loaded，防止等待锁期间
           被其他线程完成加载
        3. 验证 LoRA 模型目录及必要文件存在
        4. 检测并配置推理设备
        5. 加载分词器（优先从本地 LoRA 目录加载）
        6. 加载基座模型（二分类头，num_labels=2）
        7. 对齐 embedding 层尺寸（tokenizer 词表可能扩充）
        8. 注入 LoRA 适配器权重
        9. CUDA 设备上 merge_and_unload 消除 LoRA 推理开销
        10. 切换到 eval 模式（关闭 dropout 等）

    异常处理:
        加载失败时，将异常信息存入 _load_error 并标记 _loaded=True，
        后续调用 _ensure_model_loaded() 会抛出包含详细信息的 RuntimeError。
    """
    global _model, _tokenizer, _device, _loaded, _load_error

    # 获取锁，确保同一时间只有一个线程执行加载逻辑
    with _lock:
        # 双重检查锁定（Double-Checked Locking）：
        # 在当前线程等待锁的过程中，可能已有其他线程完成了模型加载
        if _loaded:
            return

        try:
            # —— 验证模型目录和必要文件 ——
            if not os.path.isdir(LORA_MODEL_DIR):
                raise FileNotFoundError(
                    f"LoRA 模型目录不存在: {LORA_MODEL_DIR}\n"
                    f"请先运行 train_roberta_tcm_intent.py 进行模型微调训练。"
                )

            # 检查 LoRA 适配器的两个核心文件
            # adapter_config.json:  LoRA 配置（r, alpha, target_modules 等）
            # adapter_model.safetensors: LoRA 权重（A·B 低秩矩阵 + classifier）
            required_files = ["adapter_config.json", "adapter_model.safetensors"]
            for f in required_files:
                if not os.path.isfile(os.path.join(LORA_MODEL_DIR, f)):
                    raise FileNotFoundError(
                        f"LoRA 模型文件缺失: {f}\n"
                        f"请确保训练已成功完成并保存了所有必要文件。"
                    )

            # —— 设备检测 ——
            _device = _get_device()
            print(f"🔧 中医意图识别 RoBERTa 模型加载中... (设备: {_device})")

            # —— 加载分词器 ——
            # 优先从 LoRA 保存目录加载，确保与训练时的 tokenizer 完全一致
            # （包括可能添加的特殊 token、vocab 大小等）
            _tokenizer = AutoTokenizer.from_pretrained(LORA_MODEL_DIR)
            print(f"   ✅ 分词器加载完成 (词表大小: {_tokenizer.vocab_size})")

            # —— 加载基座模型 ——
            # fp16 精度：CUDA 设备上可节省约 50% 显存，推理速度更快
            dtype = torch.float16 if _device in ("cuda",) else torch.float32
            base_model = AutoModelForSequenceClassification.from_pretrained(
                BASE_MODEL_NAME,
                num_labels=2,            # 二分类
                dtype=dtype,
            )

            # 词表大小对齐检查：
            # 如果训练时为 tokenizer 扩充了词表（如添加了自定义特殊 token），
            # 基座模型的 embedding 矩阵尺寸需要同步调整，否则 PeftModel 加载
            # classifier 权重时可能出现维度不匹配错误
            if len(_tokenizer) > base_model.config.vocab_size:
                base_model.resize_token_embeddings(len(_tokenizer))
                print(f"   ⚠️ 检测到 tokenizer 词表扩充 ({base_model.config.vocab_size} → {len(_tokenizer)})，"
                      f"已调整 embedding 层")

            print(f"   ✅ 基座模型加载完成")

            # —— 注入 LoRA 适配器 ——
            # PeftModel.from_pretrained(base_model, lora_dir) 会：
            #   1. 读取 adapter_config.json 获取 LoRA 配置
            #   2. 读取 adapter_model.safetensors 获取 LoRA 权重
            #   3. 在 base_model 的相应层旁路插入 A·B 矩阵并加载权重
            #   4. 加载 classifier 权重到分类头
            _model = PeftModel.from_pretrained(base_model, LORA_MODEL_DIR)

            # —— LoRA 合并（仅 CUDA） ——
            # merge_and_unload() 将 LoRA 的 A·B 矩阵计算合并到原始权重 W 中：
            #   W_merged = W + (alpha/r) * A·B
            # 合并后模型变为普通 PyTorch 模型（非 PeftModel），推理时无需
            # 额外计算 A·B，速度更快。
            # 但该操作在 macOS (MPS/CPU) 上可能导致 segfault（PyTorch 与
            # PEFT 权重重组在非 CUDA 后端不够稳定），因此仅在 CUDA 上执行。
            if _device == "cuda":
                _model = _model.merge_and_unload()
                print(f"   ✅ LoRA 适配器已合并到基座模型")
            else:
                print(f"   ⚠️ 跳过 merge_and_unload（{_device} 设备兼容性），保留 PeftModel 结构")

            # 将模型移动到推理设备
            _model.to(_device)
            # 切换到评估模式：
            # - 关闭 Dropout（所有神经元都参与计算）
            # - 关闭 BatchNorm 的统计更新（使用训练时累积的统计值）
            _model.eval()
            print(f"   ✅ LoRA 适配器加载完成")

            _loaded = True
            print(f"🎉 中医意图识别 RoBERTa 模型加载成功")

        except Exception as e:
            # 捕获所有异常，保存错误信息供后续调用抛出
            _load_error = str(e)
            _loaded = True  # 标记已尝试加载，防止无限重试
            raise


def _ensure_model_loaded():
    """
    确保模型已正确加载，否则抛出清晰的错误信息。

    调用时机:
        在 predict_tcm_intent() 和 predict_with_confidence()
        的入口处调用，确保模型在首次推理前完成加载。

    异常:
        RuntimeError: 模型加载失败或尚未初始化
            - 如果 _load_model() 执行过程中捕获到异常，
              会抛出包含原始错误信息的 RuntimeError
            - 如果 _loaded=True 但 _model 仍为 None
              （理论上不应发生，作为安全检查），也会抛出异常
    """
    global _model, _tokenizer

    # 如果尚未尝试加载，触发懒加载
    if not _loaded:
        try:
            _load_model()
        except Exception:
            # _load_model 内部已将错误信息存入 _load_error 并标记 _loaded=True
            raise RuntimeError(
                f"中医意图识别 RoBERTa 模型加载失败: {_load_error or '未知错误'}"
            ) from None

    # 安全检查：_loaded=True 但模型仍为 None（理论上不应发生）
    if _model is None or _tokenizer is None:
        if _load_error:
            raise RuntimeError(
                f"中医意图识别 RoBERTa 模型未成功初始化: {_load_error}"
            )
        raise RuntimeError(
            "中医意图识别 RoBERTa 模型未成功初始化，"
            "请先运行 train_roberta_tcm_intent.py 进行模型微调训练。"
        )


# ============================================================
# 对外推理接口
# ============================================================

def predict_tcm_intent(text: str, threshold: float = CONFIDENCE_THRESHOLD) -> bool:
    """
    判断用户输入文本是否与中医相关（二分类）。

    推理流程:
        1. 确保模型已加载（首次调用触发懒加载）
        2. 对输入文本进行 WordPiece 分词（截断+填充到 max_length）
        3. 将输入张量移动到推理设备
        4. 禁用梯度计算，执行前向传播
        5. 对 logits 做 softmax 得到概率分布
        6. 比较「是（中医）」的概率是否超过阈值

    参数:
        text:      用户输入文本（中文）
        threshold: 分类阈值，默认 0.5。
                   当「是（中医）」类别的概率 > threshold 时返回 True。
                   降低阈值可提高召回率（更少漏判），但可能增加误判。
                   提高阈值可提高精确率（更少误判），但可能增加漏判。

    返回:
        bool: True = 中医相关, False = 非中医相关

    异常:
        RuntimeError: 模型尚未训练或加载失败时抛出

    示例:
        >>> predict_tcm_intent("枸杞有什么功效")
        True

        >>> predict_tcm_intent("今天天气怎么样")
        False

        >>> predict_tcm_intent("如何提高免疫力")  # 边界模糊问题
        False  # 模型可能判为非中医（取决于训练数据分布）
    """
    _ensure_model_loaded()

    # 分词处理
    # truncation=True: 超过 max_length 的部分被截断
    # padding="max_length": 不足 max_length 的部分用 [PAD] 填充
    # return_tensors="pt": 返回 PyTorch 张量格式
    inputs = _tokenizer(
        text,
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH,
        return_tensors="pt",
    ).to(_device)  # 移动到推理设备

    # 推理阶段禁用梯度计算
    # torch.no_grad() 减少内存占用，加速推理
    with torch.no_grad():
        outputs = _model(**inputs)
        logits = outputs.logits                 # shape: (1, 2)
        probs = torch.softmax(logits, dim=-1)   # 概率分布: [[P(否), P(是)]]
        # probs[0][0] = 标签 0（否）的概率
        # probs[0][1] = 标签 1（是）的概率
        is_zhongyi_prob = probs[0][1].item()     # 提取 Python 标量

    return is_zhongyi_prob > threshold


def predict_with_confidence(text: str) -> Tuple[bool, float]:
    """
    判断用户输入是否与中医相关，同时返回预测的置信度。

    与 predict_tcm_intent 的区别:
        - predict_tcm_intent 返回 bool，可选调整阈值
        - predict_with_confidence 返回 (bool, float)，使用默认阈值 0.5，
          同时返回模型对预测结果的置信度，方便上层做进一步处理

    参数:
        text: 用户输入文本（中文）

    返回:
        (is_zhongyi: bool, confidence: float):
            - is_zhongyi: True=中医相关, False=非中医相关
            - confidence: 模型对预测类别的置信度 (0.0 ~ 1.0)
                          （注意：不是校准后的概率，而是 softmax 输出值）

    异常:
        RuntimeError: 模型尚未训练或加载失败时抛出

    示例:
        >>> is_zhongyi, confidence = predict_with_confidence("枸杞的功效")
        >>> print(f"中医相关: {is_zhongyi}, 置信度: {confidence:.4f}")
        中医相关: True, 置信度: 0.9523

        >>> is_zhongyi, confidence = predict_with_confidence("考驾照科二怎么过")
        >>> print(f"中医相关: {is_zhongyi}, 置信度: {confidence:.4f}")
        中医相关: False, 置信度: 0.9812
    """
    _ensure_model_loaded()

    # 分词
    inputs = _tokenizer(
        text,
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH,
        return_tensors="pt",
    ).to(_device)

    # 前向推理
    with torch.no_grad():
        outputs = _model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)
        is_zhongyi_prob = probs[0][1].item()   # 标签"是"的概率
        not_zhongyi_prob = probs[0][0].item()   # 标签"否"的概率

    # 返回预测结果和对应置信度
    if is_zhongyi_prob > not_zhongyi_prob:
        return True, is_zhongyi_prob
    else:
        return False, not_zhongyi_prob


# ============================================================
# 模块自测（直接运行此文件时执行）
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Chinese-RoBERTa-wwm-ext + LoRA 中医意图识别测试")
    print("=" * 60)

    # 测试用例: (输入文本, 预期标签)
    # True=中医相关, False=非中医相关
    test_cases = [
        ("安神助眠茶配方", True),
        ("小红书怎么涨粉", False),
        ("玉屏风散的功效", True),
        ("怎么瘦大腿", False),
        ("讲讲解表的药材有哪些", True),
        ("黑洞是怎么形成的", False),
        ("逍遥丸主要治什么", True),
        ("身份证过期了怎么换", False),
        ("枸杞泡水有什么好处", True),
        ("考驾照科二怎么过", False),
        ("请介绍《黄帝内经》的主要内容", True),
        ("外卖超时怎么投诉", False),
        ("二陈汤的组成是什么", True),
        ("大学生要不要考研", False),
    ]

    correct = 0
    total = len(test_cases)

    for text, expected in test_cases:
        try:
            # 使用 predict_with_confidence 获取详细预测结果
            is_zhongyi, confidence = predict_with_confidence(text)
            is_correct = (is_zhongyi == expected)
            if is_correct:
                correct += 1
            status = "✅" if is_correct else "❌"
            expected_str = "是（中医）" if expected else "否（非中医）"
            predicted_str = "是（中医）" if is_zhongyi else "否（非中医）"
            print(f"  {status} 期望: {expected_str} | 预测: {predicted_str} "
                  f"(置信度: {confidence:.4f}) | {text}")
        except Exception as e:
            print(f"  ❌ 错误: {e} | {text}")

    print("-" * 60)
    accuracy = correct / total * 100 if total > 0 else 0
    print(f"  准确率: {correct}/{total} ({accuracy:.1f}%)")
    print("=" * 60)
