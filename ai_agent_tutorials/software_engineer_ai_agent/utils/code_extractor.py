# utils/code_extractor.py
import re

def extract_code_block(full_text, language='python'):
    """
    Extract code block from the full text, removing any markdown or LLM response text.
    
    Args:
        full_text (str): The full text containing the code block
        language (str, optional): The programming language. Defaults to 'python'.
    
    Returns:
        str: Extracted code block
    """
    # Regular expression to match code blocks
    code_block_pattern = fr'```{language}\n(.*?)```'
    match = re.search(code_block_pattern, full_text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    # If no code block found, return the entire text (assuming it's pure code)
    return full_text.strip()