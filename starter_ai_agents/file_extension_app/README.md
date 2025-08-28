# File Extension Guesser

A command-line tool that analyzes files in a directory and adds the appropriate file extension to them based on their content.

## Description

This script iterates through all the files in a specified directory. For each file that does not have a file extension, it uses `python-magic` to determine the file's MIME type. It then uses this MIME type to guess the correct file extension and renames the file accordingly.

The script will ignore:
- Directories
- Files that already have an extension
- Shell scripts

## Usage

1.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the script:**

    ```bash
    python main.py /path/to/your/directory
    ```

    Replace `/path/to/your/directory` with the actual path to the directory containing the files you want to analyze.
