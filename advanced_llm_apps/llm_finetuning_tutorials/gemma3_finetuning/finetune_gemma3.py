import torch
from unsloth import FastModel  # Unsloth fast loader + training utils
from unsloth.chat_templates import get_chat_template, standardize_sharegpt
from datasets import load_dataset  # Hugging Face datasets
from trl import SFTTrainer  # Supervised fine-tuning trainer
from transformers import TrainingArguments  # Training hyperparameters

# Minimal config (GPU expected). Adjust sizes: 270m, 1b, 4b, 12b, 27b
MODEL_NAME = "unsloth/gemma-3-270m-it"
MAX_SEQ_LEN = 2048
LOAD_IN_4BIT = True  # 4-bit quantized loading for low VRAM
LOAD_IN_8BIT = False  # 8-bit quantized loading for low VRAM
FULL_FINETUNING = False  # LoRA adapters (efficient) instead of full FT


def load_model_and_tokenizer():
    # Load Gemma 3 + tokenizer with desired context/quantization
    model, tokenizer = FastModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LEN,
        load_in_4bit=LOAD_IN_4BIT,
        load_in_8bit=LOAD_IN_8BIT,
        full_finetuning=FULL_FINETUNING,
    )

    if not FULL_FINETUNING:
        # Add LoRA adapters on attention/MLP projections (PEFT)
        model = FastModel.get_peft_model(
            model,
            r=16,
            target_modules=[
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj",
            ],
        )

    # Apply Gemma 3 chat template for correct conversation formatting
    tokenizer = get_chat_template(tokenizer, chat_template="gemma-3")
    return model, tokenizer


def prepare_dataset(tokenizer):
    # Load ShareGPT-style conversations and standardize schema
    dataset = load_dataset("mlabonne/FineTome-100k", split="train")
    dataset = standardize_sharegpt(dataset)
    # Render each conversation into a single training string
    dataset = dataset.map(
        lambda ex: {"text": [tokenizer.apply_chat_template(c, tokenize=False) for c in ex["conversations"]]},
        batched=True,
    )
    return dataset


def train(model, dataset):
    # Choose precision based on CUDA capabilities
    use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    use_fp16 = torch.cuda.is_available() and not use_bf16

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LEN,
        args=TrainingArguments(
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_steps=5,
            max_steps=60,
            learning_rate=2e-4,
            bf16=use_bf16,
            fp16=use_fp16,
            logging_steps=1,
            output_dir="outputs",
        ),
    )
    trainer.train()


def main():
    # 1) Load model/tokenizer, 2) Prep data, 3) Train, 4) Save weights
    model, tokenizer = load_model_and_tokenizer()
    dataset = prepare_dataset(tokenizer)
    train(model, dataset)
    model.save_pretrained("finetuned_model")


if __name__ == "__main__":
    main()


