"""
Utility functions for text processing, tokenization, and chunking.
"""
from typing import List, Optional, Any


def count_tokens(text: str, encoding=None) -> int:
    """
    Count the number of tokens in the given text.
    
    Args:
        text (str): The text to count tokens for
        encoding: Optional tokenizer/encoding to use
        
    Returns:
        int: Number of tokens in the text
    """
    if not text:
        return 0
        
    if encoding:
        try:
            return len(encoding.encode(text))
        except Exception:
            # Fallback to character-based approximation if encoding fails
            pass
            
    # Rough approximation: ~3 characters per token for English text
    return len(text) // 3


def chunk_text_by_tokens(text: str, target_chunk_size: int, encoding=None) -> List[str]:
    """
    Split text into chunks based on token count.
    
    Args:
        text (str): The text to chunk
        target_chunk_size (int): Target token count per chunk
        encoding: Optional tokenizer/encoding to use
        
    Returns:
        List[str]: List of text chunks
    """
    if not text:
        return []
        
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    
    # Handle case where paragraphs are too long by splitting them further
    processed_paragraphs = []
    for para in paragraphs:
        if count_tokens(para, encoding) > target_chunk_size:
            # Split long paragraphs by sentences
            sentences = para.replace('. ', '.\n').split('\n')
            processed_paragraphs.extend(sentences)
        else:
            processed_paragraphs.append(para)
    
    # Now combine paragraphs into chunks of appropriate token size
    chunks = []
    current_chunk = []
    current_token_count = 0
    
    for para in processed_paragraphs:
        para_token_count = count_tokens(para, encoding)
        
        # If adding this paragraph exceeds the target size and we already have content,
        # finalize the current chunk and start a new one
        if current_token_count + para_token_count > target_chunk_size and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = []
            current_token_count = 0
            
        # Handle paragraphs that are individually larger than target size
        if para_token_count > target_chunk_size:
            # If we have accumulated content, save it first
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_token_count = 0
                
            # Add the oversized paragraph as its own chunk
            chunks.append(para)
        else:
            current_chunk.append(para)
            current_token_count += para_token_count
    
    # Don't forget the last chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
        
    return chunks
