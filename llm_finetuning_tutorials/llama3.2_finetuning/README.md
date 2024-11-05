## 🦙 Finetune Llama 3.2 in 30 Lines of Python

This script demonstrates how to finetune the Llama 3.2 model using the [Unsloth](https://unsloth.ai/) library, which makes the process easy and fast. You can run this example to finetune Llama 3.1 1B and 3B models for free in Google Colab.

### Features

- Finetunes Llama 3.2 model using the Unsloth library
- Implements Low-Rank Adaptation (LoRA) for efficient finetuning
- Uses the FineTome-100k dataset for training
- Configurable for different model sizes (1B and 3B)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd llama3.2_finetuning
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Open the script in Google Colab or your preferred Python environment.

2. Run the script to start the finetuning process:

```bash
# Run the entire script
python finetune_llama3.2.py
```

3. The finetuned model will be saved in the "finetuned_model" directory.

## How it Works

1. **Model Loading**: The script loads the Llama 3.2 3B Instruct model using Unsloth's FastLanguageModel.

2. **LoRA Setup**: Low-Rank Adaptation is applied to specific layers of the model for efficient finetuning.

3. **Data Preparation**: The FineTome-100k dataset is loaded and preprocessed using a chat template.

4. **Training Configuration**: The script sets up the SFTTrainer with specific training arguments.

5. **Finetuning**: The model is finetuned on the prepared dataset.

6. **Model Saving**: The finetuned model is saved to disk.

## Configuration

You can modify the following parameters in the script:

- `model_name`: Change to "unsloth/Llama-3.1-1B-Instruct" for the 1B model
- `max_seq_length`: Adjust the maximum sequence length
- `r`: LoRA rank
- Training hyperparameters in `TrainingArguments`

## Customization

- To use a different dataset, replace the `load_dataset` function call with your desired dataset.
- Adjust the `target_modules` in the LoRA setup to finetune different layers of the model.
- Modify the chat template in `get_chat_template` if you're using a different conversational format.

## Running on Google Colab

1. Open a new Google Colab notebook.
2. Copy the entire script into a code cell.
3. Add a cell at the beginning to install the required libraries:

```
!pip install torch transformers datasets trl unsloth
```

4. Run the cells to start the finetuning process.

## Notes

- This script is optimized for running on Google Colab's free tier, which provides access to GPUs.
- The finetuning process may take some time, depending on the model size and the available computational resources.
- Make sure you have enough storage space in your Colab instance to save the finetuned model.