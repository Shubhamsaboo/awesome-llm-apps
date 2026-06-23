import json
import logging
from typing import Optional, Dict, Any
import requests
from .llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class LocalProvider(LLMProvider):
    """Local LLM provider using Ollama or compatible API"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2", 
                 temperature: float = 0.3, max_tokens: int = 2000):
        super().__init__(model, temperature, max_tokens)
        self.base_url = base_url.rstrip("/")
        self.api_endpoint = f"{self.base_url}/api/generate"
        self.connection_checked = False
        self.is_available = False
        
    def _check_connection(self) -> bool:
        """Check if local LLM is running (lazy check)"""
        if self.connection_checked:
            return self.is_available
            
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            self.is_available = response.status_code == 200
            self.connection_checked = True
            return self.is_available
        except Exception as e:
            logger.warning(f"Local LLM not available at {self.base_url}: {str(e)}")
            self.connection_checked = True
            self.is_available = False
            return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using local LLM"""
        try:
            if not self._check_connection():
                raise ConnectionError(f"Local LLM not available at {self.base_url}. Make sure Ollama is running.")
            
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "temperature": self.temperature,
                "stream": False,
            }
            
            response = requests.post(self.api_endpoint, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Local LLM generation error: {str(e)}")
            raise
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate JSON response using local LLM"""
        try:
            json_prompt = f"{prompt}\n\nRespond ONLY with valid JSON, no markdown formatting."
            response_text = self.generate(json_prompt, system_prompt)
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}, response: {response_text[:200]}")
            raise
        except Exception as e:
            logger.error(f"Local LLM JSON generation error: {str(e)}")
            raise
