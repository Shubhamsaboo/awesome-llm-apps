"""
Configuration for NeuroMAS training and evaluation.

One uniform protocol is applied to every benchmark. The only task-type-dependent
quantities are the generation length and the reward / answer extraction
(multiple-choice vs. code), which are intrinsic to the answer format.

All values can be overridden through environment variables (see run.py for the
smoke-test presets).
"""
import os

# ---- Base model (frozen backbone) ----
MODEL_NAME = os.environ.get("MODEL_NAME", "Qwen/Qwen3-0.6B")
SEED = 42

# ---- LoRA (one adapter per NeuroMAS node) ----
LORA_RANK = 8
LORA_ALPHA = 16
LORA_DROPOUT = 0.05
LORA_TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj"]

# ---- Optimisation (REINFORCE + per-node EMA reward baseline) ----
LR = 2e-5
GRAD_CLIP = 1.0
EMA_DECAY = 0.9                  # per-node reward baseline decay

# ---- Evaluation protocol ----
EVAL_SIZE = int(os.environ.get("EVAL_SIZE", 200))      # global eval cap; per-dataset targets in tasks.py
TRAIN_SIZE = int(os.environ.get("TRAIN_SIZE", 300))
DEV_SIZE = int(os.environ.get("DEV_SIZE", 30))
CKPT_EVERY = int(os.environ.get("CKPT_EVERY", 50))     # dev-eval cadence for best-checkpoint selection
DEV_EVAL_N = int(os.environ.get("DEV_EVAL_N", 30))     # dev subset size used during training

# ---- RL step schedule for progressive growth ----
# Phase 1 trains NeuroMAS-3 from scratch; each later phase grows the topology
# and continues training with the same terminal reward.
STEPS_NEUROMAS = (
    int(os.environ.get("STEPS_NM_P1", 1000)),          # -> NeuroMAS-3 (topology [1, 1])
    int(os.environ.get("STEPS_NM_P2", 800)),           # -> NeuroMAS-5 (topology [2, 2])
    int(os.environ.get("STEPS_NM_P3", 800)),           # -> NeuroMAS-7 (topology [2, 2, 2])
)

# ---- Generation length profiles (intrinsic to answer format) ----
# Multiple-choice answers are short; code completion needs a longer budget.
TOK_MCQ_INNER = int(os.environ.get("TOK_MCQ_INNER", 250))    # non-final node (inter-agent message)
TOK_MCQ_OUTER = int(os.environ.get("TOK_MCQ_OUTER", 150))    # output aggregation node
TOK_CODE_INNER = int(os.environ.get("TOK_CODE_INNER", 400))
TOK_CODE_OUTER = int(os.environ.get("TOK_CODE_OUTER", 600))
SEC_MAX_CHARS = 200             # per-recipient routed-message truncation


def device():
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


def seed_all():
    import random, torch
    random.seed(SEED); torch.manual_seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)
