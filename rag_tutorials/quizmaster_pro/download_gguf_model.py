import os
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import HfHubHTTPError # Corrected import
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Model details
REPO_ID = "TheBloke/Mistral-7B-Instruct-v0.1-GGUF"
FILENAME = "mistral-7b-instruct-v0.1.Q8_0.gguf"
LOCAL_DIR = "."  # Download to the current directory (project root)

def download_model():
    """Downloads the specified GGUF model from Hugging Face Hub."""
    model_path = os.path.join(LOCAL_DIR, FILENAME)

    if os.path.exists(model_path):
        logger.info(f"Model '{FILENAME}' already exists at '{model_path}'. Skipping download.")
        return model_path

    logger.info(f"Downloading '{FILENAME}' from '{REPO_ID}' to '{LOCAL_DIR}'...")
    
    try:
        downloaded_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_dir=LOCAL_DIR,
            local_dir_use_symlinks=False,  # As specified by user
            resume_download=True
        )
        logger.info(f"Successfully downloaded model to: {downloaded_path}")
        return downloaded_path
    except HfHubHTTPError as e:
        logger.error(f"HTTP error during download: {e}. "
                     f"This might be due to network issues or if the file/repo is not found.")
        logger.error(f"Please ensure you can access Hugging Face Hub and the repository '{REPO_ID}' exists.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during download: {e}", exc_info=True)
    
    return None

if __name__ == "__main__":
    logger.info("Starting GGUF model download process...")
    final_path = download_model()
    if final_path:
        logger.info(f"Model download process finished. Model is available at: {final_path}")
    else:
        logger.error("Model download process failed. Please check the logs for details.")
        logger.info("You might need to install huggingface_hub: pip install huggingface-hub")