"""
Chinese-RoBERTa-wwm-ext + LoRA 中医意图识别 —— 训练脚本
=========================================================

功能概述:
    基于 hfl/chinese-roberta-wwm-ext 预训练模型，使用 LoRA
    （Low-Rank Adaptation，低秩适配）进行轻量化微调，训练
    中医意图二分类器（是/否中医相关问题）。

LoRA 原理与优势:
    1. 冻结原模型全部参数（约 110M 参数）
    2. 在 Transformer 层的 Q（Query）和 V（Value）注意力矩阵
       旁路插入低秩分解矩阵 A·B（r << d_model）
    3. 仅训练 A、B 矩阵和分类头（classifier），参数量约 0.3M
    4. 效果: 大幅降低显存占用（~90%）和训练时间，同时保持
       接近全量微调的效果

数据来源:
    __007__fine_tune/intent_recognition_data/roberta_tcm_intent.csv
    格式: text,target（target 为 "是" 或 "否"）
    由 generate_training_data.py 自动生成（约 4000 条）

训练流程:
    1. 加载 CSV 数据，分层拆分为训练集（80%）和验证集（20%）
    2. 加载基座模型和分词器，配置 LoRA 适配器
    3. 对文本进行分词、截断、填充
    4. 创建 HuggingFace Trainer（含早停回调）
    5. 训练（支持 CUDA/MPS/CPU，自动启用混合精度）
    6. 评估：精确率、召回率、F1、混淆矩阵、分类报告
    7. 保存 LoRA 适配器权重到指定目录
    8. 用典型输入做手动测试

用法:
    # 从项目根目录运行
    python -m __007__fine_tune.chineserobertawwmext_zhongyi_recognition.train_roberta_tcm_intent

    # 或在当前目录直接运行
    python train_roberta_tcm_intent.py

输出（保存到 __007__fine_tune/model/roberta_tcm_intent_lora/）:
    - adapter_config.json       LoRA 适配器配置（秩、alpha、目标模块等）
    - adapter_model.safetensors LoRA 适配器权重（低秩矩阵 A·B + classifier）
    - tokenizer 相关文件        分词器配置（vocab、special_tokens 等）

注意事项:
    - 训练前需先运行 generate_training_data.py 生成 roberta_tcm_intent.csv
    - 首次运行会自动从 HuggingFace 下载基座模型（约 400MB），需要网络连接
    - macOS MPS 训练模式下模型需手动移动到 MPS 设备（Trainer 不会自动处理）
    - torch_compile 已禁用（在某些环境下可能报错）
"""

import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import torch
# 导入 sklearn 评估指标
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
)
from sklearn.model_selection import train_test_split  # 分层拆分训练/验证集
from datasets import Dataset                           # HuggingFace 数据集格式
from transformers import (
    AutoTokenizer,                        # 自动加载与模型匹配的分词器
    AutoModelForSequenceClassification,   # 自动加载分类模型（加二分类头）
    Trainer,                              # HuggingFace 训练器（封装训练循环）
    TrainingArguments,                    # 训练器配置（超参数、策略等）
    EarlyStoppingCallback,                # 早停回调（验证集 loss 不再下降则停止）
)
from peft import (
    LoraConfig,        # LoRA 配置（秩、alpha、dropout、目标模块）
    get_peft_model,    # 将 LoRA 适配器注入基座模型
    TaskType,          # 任务类型枚举（SEQ_CLS = 序列分类）
)

# 确保能导入项目内部模块（如 common.path_utils）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.path_utils import get_file_path

# 忽略 transformers 的一些冗余警告
warnings.filterwarnings("ignore")

# ============================================================
# 路径配置
# ============================================================

# 训练数据路径（CSV 格式，text 列为输入文本，target 列为标签）
DATA_FILE = get_file_path("__007__fine_tune/intent_recognition_data/roberta_tcm_intent.csv")

# 模型保存目录（LoRA 适配器权重 + tokenizer 配置）
MODEL_OUTPUT_DIR = get_file_path("__007__fine_tune/model/roberta_tcm_intent_lora")

# 预训练基座模型名称（HuggingFace 模型库标识）
# hfl/chinese-roberta-wwm-ext: 哈工大讯飞联合发布的
# 中文 RoBERTa 模型，使用全词掩码（WWM）训练
BASE_MODEL_NAME = "hfl/chinese-roberta-wwm-ext"

# ============================================================
# 训练超参数
# ============================================================

# —— 数据拆分参数 ——
TRAIN_SIZE = 0.8        # 训练集比例（剩余 20% 作为验证集）
RANDOM_SEED = 42        # 随机种子，确保数据拆分和模型初始化可复现

# —— 分词参数 ——
MAX_LENGTH = 128        # 最大输入序列长度（token 数）
                        # 中医问题通常较短，128 足够覆盖绝大多数场景

# —— LoRA 配置 ——
# LoRA 的核心思想：对于预训练权重矩阵 W ∈ R^{d×k}，
# 其更新 ΔW 可分解为低秩矩阵 A·B，其中 A ∈ R^{d×r}, B ∈ R^{r×k}, r << min(d,k)
LORA_R = 8              # LoRA 秩（rank），决定了可训练参数量
                        # r=8 是常用的默认值，在效果和效率间取得平衡
LORA_ALPHA = 16         # LoRA 缩放系数，实际学习率缩放比例为 alpha/r
                        # 通常设为 2 * r，使缩放因子 = 2
LORA_DROPOUT = 0.1      # LoRA 层的 dropout 概率，防止适配器过拟合
LORA_TARGET_MODULES = ["query", "value"]  # 对注意力层的 Q（Query）和 V（Value）
                        # 矩阵插入 LoRA 适配器，这是经验上效果最好的选择

# —— 训练参数 ——
NUM_EPOCHS = 5                  # 最大训练轮数（早停触发时可能提前结束）
BATCH_SIZE = 16                 # 训练/验证每批样本数
LEARNING_RATE = 2e-4            # LoRA 微调推荐学习率（比全量微调 5e-5 更高）
WEIGHT_DECAY = 0.01             # 权重衰减（L2 正则化），防止过拟合
WARMUP_RATIO = 0.1              # warmup 步数占比，前 10% 步数线性增加学习率
EVAL_STEPS = 50                 # 每 50 步在验证集上评估一次
SAVE_STEPS = 100                # 每 100 步保存一个 checkpoint
LOGGING_STEPS = 20              # 每 20 步打印一次训练日志
EARLY_STOPPING_PATIENCE = 3     # 早停耐心值：验证集 loss 连续 3 次评估不下降则停止
FP16 = torch.cuda.is_available()  # 有 GPU（CUDA）则启用 fp16 混合精度训练
                                   # fp16 可降低约 50% 显存占用，几乎不影响精度

# —— 设备检测 ——
def _detect_device() -> str:
    """
    检测可用的训练设备，按优先级选择。

    检测顺序:
        1. CUDA（NVIDIA GPU）—— 性能最优，支持 fp16 混合精度
        2. MPS（Apple Silicon GPU on macOS）—— 部分算子可能不兼容
        3. CPU —— 最终的兜底方案，速度最慢

    返回:
        str: 设备标识符（"cuda", "mps", 或 "cpu"）
    """
    if torch.cuda.is_available():
        return "cuda"
    # macOS 上检查 Apple Silicon GPU (MPS) 是否可用
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        try:
            # 尝试验证 MPS 是否真正可用（某些 PyTorch 版本 MPS 后端
            # 可能已注册但实际不可用）
            _ = torch.zeros(1).to("mps")
            return "mps"
        except Exception:
            pass  # MPS 不可用，回退到 CPU
    return "cpu"

TRAIN_DEVICE = _detect_device()
IS_MPS = (TRAIN_DEVICE == "mps")  # MPS 模式下需要手动将模型移动到设备

# ============================================================
# 工具函数
# ============================================================


def load_and_prepare_data(data_file: str):
    """
    加载 CSV 训练数据，转换为 HuggingFace Dataset 格式。

    数据处理流程:
        1. 读取 CSV（英文逗号分隔，中文文本中的全角逗号不冲突）
        2. 标签编码: "是" → 1（正类，中医相关）, "否" → 0（负类，非中医）
        3. 验证标签合法性（确保无未知标签值）
        4. 统计原始标签分布
        5. 分层拆分（stratify=label）为训练集和验证集，
           保证两集合的标签分布比例一致
        6. 标签转为 Python int（避免 datasets 库类型推断问题）
        7. 包装为 HuggingFace Dataset 对象

    参数:
        data_file: CSV 数据文件的完整路径

    返回:
        train_dataset: HuggingFace Dataset（训练集）
        val_dataset:   HuggingFace Dataset（验证集）
        label_counts:  pandas Series，各类别的样本数统计

    异常:
        ValueError: 数据中存在无法映射的未知标签值时抛出
    """
    print("\n" + "=" * 60)
    print("📊 加载训练数据")
    print("=" * 60)

    # 读取 CSV，英文逗号分隔（中文文本中为全角逗号"、"，不会冲突）
    df = pd.read_csv(data_file, sep=",")
    print(f"   原始数据: {len(df)} 条")

    # 标签编码：将中文标签映射为数值
    label_map = {"否": 0, "是": 1}
    df["label"] = df["target"].map(label_map)

    # 检查是否有无法映射的标签（例如 target 列包含 "是"/"否" 以外的值）
    if df["label"].isna().any():
        invalid_labels = df[df["label"].isna()]["target"].unique().tolist()
        raise ValueError(f"发现无法解析的标签值: {invalid_labels}")

    # 统计各类别样本数及占比
    label_counts = df["label"].value_counts().sort_index()
    print(f"   标签分布:")
    for lbl_id, cnt in label_counts.items():
        lbl_name = "是" if lbl_id == 1 else "否"
        print(f"     [{lbl_name}]: {cnt} ({100*cnt/len(df):.1f}%)")

    # 分层拆分训练集和验证集
    # stratify=df["label"] 确保两集合的正负样本比例与原始数据一致
    train_df, val_df = train_test_split(
        df,
        train_size=TRAIN_SIZE,    # 80% 训练，20% 验证
        random_state=RANDOM_SEED,  # 固定随机种子保证可复现
        stratify=df["label"],
    )
    print(f"\n   拆分后 => 训练集: {len(train_df)} 条, 验证集: {len(val_df)} 条")

    # 将 label 显式转为 Python int 类型
    # datasets 库从 list 推断特征类型时可能将 numpy.int64 误判，
    # 显式转为 Python int 可避免此问题
    train_labels = [int(l) for l in train_df["label"].tolist()]
    val_labels = [int(l) for l in val_df["label"].tolist()]

    # 构建 HuggingFace Dataset（字典格式）
    # Dataset.from_dict 会自动推断 features 类型（string 和 int64）
    train_dataset = Dataset.from_dict({
        "text": train_df["text"].tolist(),
        "label": train_labels,
    })
    val_dataset = Dataset.from_dict({
        "text": val_df["text"].tolist(),
        "label": val_labels,
    })

    print(f"   ✅ 数据准备完成")
    return train_dataset, val_dataset, label_counts


def build_model_and_tokenizer():
    """
    加载基座模型和分词器，配置 LoRA 适配器。

    构建步骤:
        1. 加载 hfl/chinese-roberta-wwm-ext 分词器（WordPiece 分词）
        2. 加载预训练模型并添加二分类头（num_labels=2）
        3. 检查并补全 pad_token（防止 tokenizer 版本差异导致缺失）
        4. 配置 LoRA 参数（秩 r、缩放 alpha、dropout、目标模块等）
        5. 将 LoRA 适配器注入基座模型
        6. 统计并打印可训练参数量

    LoRA 配置说明:
        - target_modules=["query", "value"]:
          仅对注意力层的 Query 和 Value 投影矩阵插入 LoRA，
          Key 和 Output 投影保持原样。这是常用的高效配置。
        - modules_to_save=["classifier"]:
          classification head（分类头）是随机初始化的，需要
          全量训练而非 LoRA 适配。此参数确保分类头参数被
          完整保存和加载。

    返回:
        model:     PeftModel（注入 LoRA 适配器后的模型）
        tokenizer: AutoTokenizer（中文 RoBERTa 分词器）
    """
    print("\n" + "=" * 60)
    print("🤖 加载模型与分词器")
    print("=" * 60)
    print(f"   基座模型: {BASE_MODEL_NAME}")

    # —— 加载分词器 ——
    # hfl/chinese-roberta-wwm-ext 使用 WordPiece 分词，
    # 词表约 21128 个 token（与 BERT-base-chinese 一致）
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)
    print(f"   分词器词表大小: {tokenizer.vocab_size}")

    # —— 加载分类模型 ——
    # num_labels=2: 二分类（标签 0="否", 1="是"）
    # torch_dtype: 有 GPU 则加载 fp16 精度模型，节省显存和加速训练
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL_NAME,
        num_labels=2,
        torch_dtype=torch.float16 if FP16 else torch.float32,
    )

    # pad_token 兼容性检查：
    # hfl/chinese-roberta-wwm-ext 基于 BERT 架构，通常已有 pad_token，
    # 但某些 tokenizer 版本可能存在差异，做防御性处理
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token if tokenizer.eos_token is not None else "[PAD]"
        # 如果使用了自定义的 "[PAD]" 作为 pad_token，需同步调整 embedding 层
        if tokenizer.pad_token == "[PAD]":
            tokenizer.add_special_tokens({"pad_token": "[PAD]"})
            model.resize_token_embeddings(len(tokenizer))

    # 确保模型配置中的 pad_token_id 与 tokenizer 一致
    model.config.pad_token_id = tokenizer.pad_token_id

    # —— 配置 LoRA 适配器 ——
    # LoraConfig 定义了 LoRA 的核心参数：
    #   r:             低秩分解的秩，越小参数越少
    #   lora_alpha:    缩放系数，实际缩放 = alpha / r
    #   lora_dropout:  适配器层的 dropout
    #   target_modules: 对哪些子层注入 LoRA
    #   modules_to_save: 除 LoRA 适配器外还需完整保存的模块
    lora_config = LoraConfig(
        task_type=TaskType.SEQ_CLS,      # 序列分类任务
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGET_MODULES,
        # classification head 需要全量训练和保存（随机初始化）
        modules_to_save=["classifier"],
    )

    # 将 LoRA 适配器注入基座模型
    # get_peft_model 会：
    #   - 冻结基座模型的所有参数（requires_grad=False）
    #   - 在 target_modules 指定的层旁路插入 A·B 低秩矩阵
    #   - 标记 A、B 矩阵和 modules_to_save 中的参数为可训练
    model = get_peft_model(model, lora_config)

    # 统计可训练参数和总参数
    # 可训练参数 ≈ r * (d_model + d_k) * num_layers * 2（Q和V各一个适配器）
    # 对于 chinese-roberta-wwm-ext：总参数 ~110M，LoRA 可训练参数 ~0.3M
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"\n   LoRA 配置:")
    print(f"     rank (r):       {LORA_R}")
    print(f"     alpha:          {LORA_ALPHA}")
    print(f"     dropout:        {LORA_DROPOUT}")
    print(f"     target_modules: {LORA_TARGET_MODULES}")
    print(f"   可训练参数:       {trainable_params:,} / {total_params:,} "
          f"({100*trainable_params/total_params:.2f}%)")
    print(f"   ✅ 模型构建完成")

    return model, tokenizer


def tokenize_function(examples, tokenizer):
    """
    分词回调函数，用于 Dataset.map() 批量处理。

    对输入文本进行:
        - 截断（truncation=True）：超过 max_length 的部分被截掉
        - 填充（padding="max_length"）：不足 max_length 的部分用 pad_token 填充
        - 返回 PyTorch 张量格式: input_ids, attention_mask

    架构说明:
        hfl/chinese-roberta-wwm-ext 基于 RoBERTa 架构（本质是 BERT 变体），
        不使用 token_type_ids（segment embeddings）；BertTokenizer 默认
        会返回 token_type_ids，但后文通过 set_format 的 columns 参数将其
        排除，确保模型不会接收到该字段。

    参数:
        examples:  批量样本字典，包含 "text" 键（文本列表）
        tokenizer: HuggingFace 分词器实例

    返回:
        dict: 包含 "input_ids" 和 "attention_mask" 的字典
    """
    return tokenizer(
        examples["text"],
        truncation=True,                   # 超长截断
        padding="max_length",              # 不足则填充到 max_length
        max_length=MAX_LENGTH,
    )


def compute_metrics(eval_pred):
    """
    计算验证集评估指标（供 Trainer 在 eval_steps 时调用）。

    计算以下指标:
        - accuracy:  准确率 = 预测正确的样本数 / 总样本数
        - precision: 精确率 = TP / (TP + FP)，预测为"是"中真正是中医的比例
        - recall:    召回率 = TP / (TP + FN)，真正中医样本中被找出的比例
        - f1:        F1 分数 = 2 * P * R / (P + R)，精确率和召回率的调和平均

    参数:
        eval_pred: EvalPrediction 对象，包含:
            - predictions: 模型输出的 logits（未归一化的分数），shape (N, 2)
            - label_ids:   真实标签，shape (N,)

    返回:
        dict: {"accuracy": ..., "precision": ..., "recall": ..., "f1": ...}
    """
    logits, labels = eval_pred
    # argmax 取 logits 最大值对应的索引作为预测类别（0="否", 1="是"）
    predictions = np.argmax(logits, axis=-1)

    # 计算基础准确率
    accuracy = accuracy_score(labels, predictions)
    # 计算二分类的精确率、召回率、F1
    # average="binary": 二分类模式，以标签 1（"是"）为正类
    # zero_division=0:  当分母为 0（如某类无样本）时返回 0 而非报错
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="binary", zero_division=0
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


# ============================================================
# 训练主流程
# ============================================================


def train():
    """
    完整的训练流程编排函数。

    训练步骤:
        1. 加载数据：读取 CSV → 标签编码 → 分层拆分 → 构建 Dataset
        2. 构建模型和分词器：加载基座模型 → 配置 LoRA → 注入适配器
        3. 数据分词：对训练集和验证集文本进行 WordPiece 分词
        4. 创建 Trainer：配置 TrainingArguments + 早停回调
        5. 训练：执行训练循环（含定期验证、checkpoint 保存）
        6. 评估：计算精确率/召回率/F1、混淆矩阵、分类报告
        7. 保存模型：持久化 LoRA 适配器权重和分词器配置
        8. 手动测试：用典型输入验证模型效果

    返回:
        model:     训练好的 PeftModel
        tokenizer: 分词器实例
    """
    # —— 1. 加载数据 ——
    train_dataset, val_dataset, _ = load_and_prepare_data(DATA_FILE)

    # —— 2. 构建模型和分词器 ——
    model, tokenizer = build_model_and_tokenizer()

    # —— 3. 数据分词 ——
    print("\n" + "=" * 60)
    print("🔪 数据分词")
    print("=" * 60)
    print(f"   最大序列长度: {MAX_LENGTH}")

    # 使用 Dataset.map() 对训练集和验证集进行批量分词
    # batched=True 启用批量处理以提高速度
    # desc 参数控制进度条显示的文字
    train_dataset = train_dataset.map(
        lambda x: tokenize_function(x, tokenizer),
        batched=True,
        desc="Tokenizing train",
    )
    val_dataset = val_dataset.map(
        lambda x: tokenize_function(x, tokenizer),
        batched=True,
        desc="Tokenizing val",
    )

    # 设置数据集格式为 PyTorch 张量
    # RoBERTa 架构不使用 token_type_ids（segment embeddings），
    # 分词器默认不生成该字段，columns 只需 input_ids、attention_mask、label
    train_dataset.set_format(
        type="torch", columns=["input_ids", "attention_mask", "label"]
    )
    val_dataset.set_format(
        type="torch", columns=["input_ids", "attention_mask", "label"]
    )
    print(f"   ✅ 分词完成")

    # —— 4. 创建 Trainer ——
    print("\n" + "=" * 60)
    print("🏋️ 开始训练")
    print("=" * 60)

    # 打印设备信息，帮助确认训练硬件环境
    if TRAIN_DEVICE == "cuda":
        print(f"   训练设备:      GPU ({torch.cuda.get_device_name(0)})")
        print(f"   GPU 显存:      {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB")
    elif TRAIN_DEVICE == "mps":
        print(f"   训练设备:      Apple Silicon GPU (MPS)")
    else:
        print(f"   训练设备:      CPU")
    print(f"   训练轮数:      {NUM_EPOCHS}")
    print(f"   Batch Size:    {BATCH_SIZE}")
    print(f"   学习率:        {LEARNING_RATE}")
    print(f"   混合精度(fp16): {'是' if FP16 else '否'}")

    # MPS 模式下需要手动将模型移动到 MPS 设备
    # CUDA 模式下 Trainer 的 fp16=True 会自动处理设备移动
    if IS_MPS:
        model = model.to("mps")
        print(f"   模型已移动到:   MPS")

    # 配置训练参数
    # TrainingArguments 是 HuggingFace 的核心配置类，涵盖了训练过程的
    # 所有超参数和策略设置
    training_args = TrainingArguments(
        output_dir=os.path.join(MODEL_OUTPUT_DIR, "checkpoints"),  # checkpoint 保存目录
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        warmup_ratio=WARMUP_RATIO,           # 学习率预热比例
        logging_dir=os.path.join(MODEL_OUTPUT_DIR, "logs"),  # TensorBoard 日志目录
        logging_steps=LOGGING_STEPS,          # 每隔多少步打印日志
        eval_strategy="steps",               # 按步数间隔进行评估（而非按 epoch）
        eval_steps=EVAL_STEPS,
        save_strategy="steps",               # 按步数间隔保存 checkpoint
        save_steps=SAVE_STEPS,
        save_total_limit=2,                  # 只保留最新的 2 个 checkpoint，避免磁盘占用
        load_best_model_at_end=True,          # 训练结束后自动加载验证集上最优的模型
        metric_for_best_model="f1",           # 以 F1 作为选择最优模型的标准
        greater_is_better=True,               # F1 越大越好
        fp16=FP16,                            # 混合精度训练（仅 CUDA 设备生效）
        dataloader_num_workers=0,             # macOS 上设为 0 避免多进程问题
        report_to=[],                         # 不上报到 wandb/mlflow 等实验追踪平台
        seed=RANDOM_SEED,
        torch_compile=False,                  # 禁用 torch.compile（某些环境不兼容）
    )

    # 早停回调：
    # 当验证集 loss 连续 early_stopping_patience 次评估都没有下降时，
    # 自动停止训练，避免过拟合，同时节省训练时间
    early_stopping = EarlyStoppingCallback(
        early_stopping_patience=EARLY_STOPPING_PATIENCE,
    )

    # 创建 Trainer 实例
    # Trainer 封装了完整的训练循环、验证、日志、checkpoint 管理
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=tokenizer,       # 用于对输入进行 tokenization
        compute_metrics=compute_metrics,  # 自定义评估指标函数
        callbacks=[early_stopping],       # 早停回调
    )

    # —— 5. 开始训练 ——
    start_time = time.time()
    # trainer.train() 执行完整的训练循环
    # 返回值 TrainOutput 包含 global_step、training_loss 等信息
    train_result = trainer.train()
    elapsed = time.time() - start_time

    print(f"\n⏱️ 训练耗时: {elapsed:.1f} 秒 ({elapsed/60:.1f} 分钟)")
    print(f"   训练步数: {train_result.global_step}")
    print(f"   训练 loss: {train_result.training_loss:.4f}")

    # —— 6. 最终评估 ——
    print("\n" + "=" * 60)
    print("📊 最终模型评估")
    print("=" * 60)

    # trainer.evaluate() 在验证集上计算所有指标（loss + compute_metrics 返回的指标）
    eval_results = trainer.evaluate()
    print(f"\n   验证集结果:")
    for key, value in sorted(eval_results.items()):
        print(f"     {key}: {value:.4f}")

    # 详细分类报告：精确率、召回率、F1（按类别）
    predictions = trainer.predict(val_dataset)
    y_pred = np.argmax(predictions.predictions, axis=-1)  # 模型预测的类别
    y_true = predictions.label_ids                         # 真实标签

    print(f"\n   分类报告:")
    print(classification_report(
        y_true, y_pred,
        target_names=["否（非中医）", "是（中医）"],
        digits=4,
    ))

    # 混淆矩阵：直观展示 TP/TN/FP/FN
    print(f"   混淆矩阵:")
    cm = confusion_matrix(y_true, y_pred)
    print(f"                 预测=否  预测=是")
    print(f"   实际=否        {cm[0][0]:5d}    {cm[0][1]:5d}")
    print(f"   实际=是        {cm[1][0]:5d}    {cm[1][1]:5d}")

    # —— 7. 保存模型 ——
    print("\n" + "=" * 60)
    print("💾 保存模型")
    print("=" * 60)

    os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)

    # 保存 LoRA 适配器权重和配置（adapter_model.safetensors + adapter_config.json）
    model.save_pretrained(MODEL_OUTPUT_DIR)
    # 保存分词器（tokenizer_config.json, vocab.txt, special_tokens_map.json 等）
    tokenizer.save_pretrained(MODEL_OUTPUT_DIR)

    # 检查保存的文件及其大小
    saved_files = os.listdir(MODEL_OUTPUT_DIR)
    total_size = 0
    for f in saved_files:
        fpath = os.path.join(MODEL_OUTPUT_DIR, f)
        if os.path.isfile(fpath):
            size = os.path.getsize(fpath)
            total_size += size
            print(f"   {f} ({size/1024:.1f} KB)")

    print(f"\n   ✅ 模型已保存到: {MODEL_OUTPUT_DIR}")
    print(f"   总大小: {total_size/1024/1024:.1f} MB")

    # —— 8. 手动测试 ——
    test_manual_examples(model, tokenizer)

    return model, tokenizer


# ============================================================
# 手动测试
# ============================================================


def test_manual_examples(model, tokenizer):
    """
    用几条典型输入做手动测试，直观感受模型效果。

    测试场景覆盖:
        - 中医方剂/药材查询（应为"是"）
        - 非中医日常问题（应为"否"）
        - 小红书运营相关（应为"否"）
        - 模糊边界问题（健康养生但不特指中医）
        - 中医经典典籍相关（应为"是"）

    推理流程:
        1. 对输入文本进行 WordPiece 分词
        2. 前向传播得到 logits
        3. softmax 转换为概率分布
        4. argmax 取最大概率对应的类别

    参数:
        model:     训练好的 PeftModel（或合并后的完整模型）
        tokenizer: 分词器实例
    """
    print("\n" + "=" * 60)
    print("🧪 手动测试示例")
    print("=" * 60)

    # 切换到评估模式（关闭 dropout, batch_norm 等训练专用行为）
    model.eval()
    # 获取模型当前所在的设备（GPU/CPU），确保输入数据在同一设备
    device = next(model.parameters()).device

    test_cases = [
        "安神助眠茶配方",
        "小红书怎么涨粉",
        "玉屏风散的功效",
        "怎么瘦大腿",
        "讲讲解表的药材有哪些",
        "黑洞是怎么形成的",
        "逍遥丸主要治什么",
        "身份证过期了怎么换",
        "枸杞泡水有什么好处",
        "考驾照科二怎么过",
        "请介绍《黄帝内经》的主要内容",
        "外卖超时怎么投诉",
        "活血化瘀的中药推荐",
        "二陈汤的组成是什么",
        "大学生要不要考研",
    ]

    for text in test_cases:
        # 分词：截断到 max_length，填充到 max_length，返回 PyTorch 张量
        inputs = tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=MAX_LENGTH,
            return_tensors="pt",
        ).to(device)  # 将输入张量移动到模型所在设备

        # 推理：禁用梯度计算，节省显存和加速
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits                 # shape: (1, 2)，两个类别的 logits
            probs = torch.softmax(logits, dim=-1)   # 将 logits 转为概率分布
            pred_label = torch.argmax(probs, dim=-1).item()  # 预测类别: 0="否", 1="是"
            confidence = probs[0][pred_label].item()          # 该预测的置信度

        readable = "是（中医）" if pred_label == 1 else "否（非中医）"
        print(f"  [{readable}] (置信度: {confidence:.4f}) | {text}")

    print("=" * 60)


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Chinese-RoBERTa-wwm-ext + LoRA 中医意图识别训练")
    print("=" * 60)
    print(f"   数据文件: {DATA_FILE}")
    print(f"   基座模型: {BASE_MODEL_NAME}")
    print(f"   输出目录: {MODEL_OUTPUT_DIR}")
    print(f"   训练轮数: {NUM_EPOCHS}")
    print(f"   Batch Size: {BATCH_SIZE}")
    print(f"   学习率: {LEARNING_RATE}")
    print(f"   设备:     {TRAIN_DEVICE}")

    # 执行完整训练流程
    train()

    print("\n🎉 训练完成！")
    print(f"   模型保存在: {MODEL_OUTPUT_DIR}")
    print(f"   推理时使用:")
    print(f"     from __007__fine_tune.chineserobertawwmext_zhongyi_recognition import predict_tcm_intent")
    print(f"     is_zhongyi = predict_tcm_intent('你的问题')")
