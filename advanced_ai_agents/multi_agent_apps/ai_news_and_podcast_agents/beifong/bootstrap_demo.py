import os
import sys
import tempfile
import requests
import zipfile
from tqdm import tqdm

DEMO_URL = "https://github.com/arun477/beifong/releases/download/v1.2.0/demo_content.zip"
TARGET_DIRS = ["databases", "podcasts"]


def ensure_empty(dir_path):
    """check if directory is empty (or create it). exit if not empty."""
    if os.path.exists(dir_path):
        if os.listdir(dir_path):
            print(f"✗ '{dir_path}' is not empty. aborting.")
            sys.exit(1)
    else:
        os.makedirs(dir_path, exist_ok=True)


def download_file(url, dest_path):
    """stream-download a file from url to dest_path with progress bar."""
    print("↓ downloading demo content...")
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    
    total_size = int(response.headers.get('content-length', 0))
    block_size = 8192
    
    with open(dest_path, "wb") as f:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Download Progress") as pbar:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))


def extract_zip(zip_path, extract_to):
    """extract zip file into extract_to (project root) with progress bar."""
    print("✂ extracting demo content...")
    
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        total_files = len(zip_ref.infolist())
        
        with tqdm(total=total_files, desc="Extraction Progress") as pbar:
            for file in zip_ref.infolist():
                zip_ref.extract(file, extract_to)
                pbar.update(1)


def main():
    print("populating demo folders…")
    for d in TARGET_DIRS:
        ensure_empty(d)
    
    with tempfile.TemporaryDirectory() as tmp:
        tmp_zip = os.path.join(tmp, "demo_content.zip")
        download_file(DEMO_URL, tmp_zip)
        extract_zip(tmp_zip, os.getcwd())
    
    print("✓ demo folders populated successfully.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n✗ Download cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
