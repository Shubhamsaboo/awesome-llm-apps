from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import logging
import json

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, model: str, temperature: float = 0.3, max_tokens: int = 2000):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.total_calls = 0  # Track total API calls
        self.total_tokens_estimate = 0  # Rough token estimate
        logger.info(f"Initialized LLM Provider: {self.model} (temp={temperature}, max_tokens={max_tokens})")
        
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using the LLM"""
        pass
    
    @abstractmethod
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate JSON response using the LLM"""
        pass
    
    def validate_response(self, response: str) -> bool:
        """Validate response is not empty"""
        is_valid = bool(response and response.strip())
        if not is_valid:
            logger.warning("⚠️ Received empty response from LLM")
        return is_valid
    
    def log_call(self, prompt_length: int, response_length: int) -> None:
        """Log API call statistics"""
        self.total_calls += 1
        # Rough estimate: 1 token ≈ 4 characters
        tokens_estimate = (prompt_length + response_length) // 4
        self.total_tokens_estimate += tokens_estimate
        
        logger.debug(f"LLM Call #{self.total_calls}:")
        logger.debug(f"  Prompt: {prompt_length} chars (~{prompt_length//4} tokens)")
        logger.debug(f"  Response: {response_length} chars (~{response_length//4} tokens)")
        logger.debug(f"  Total tokens (estimate): {self.total_tokens_estimate}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "model": self.model,
            "total_calls": self.total_calls,
            "estimated_tokens": self.total_tokens_estimate,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
    
    def extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from text that might contain markdown or other formatting.
        Utility method for providers to use.
        """
        try:
            # Try direct parsing first
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON in code blocks
        if "```" in text:
            parts = text.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1:  # Odd indices are inside code blocks
                    # Remove language identifier if present
                    if part.startswith("json"):
                        part = part[4:].strip()
                    try:
                        return json.loads(part)
                    except json.JSONDecodeError:
                        continue
        
        # Try to find JSON array or object manually
        for start_char, end_char in [('[', ']'), ('{', '}')]:
            start = text.find(start_char)
            if start >= 0:
                # Find matching closing bracket
                depth = 0
                for i in range(start, len(text)):
                    if text[i] == start_char:
                        depth += 1
                    elif text[i] == end_char:
                        depth -= 1
                        if depth == 0:
                            try:
                                return json.loads(text[start:i+1])
                            except json.JSONDecodeError:
                                break
        
        logger.warning("Could not extract valid JSON from LLM response")
        return None
