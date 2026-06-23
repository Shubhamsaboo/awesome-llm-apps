import json
import logging
import os
from typing import Optional, Dict, Any
from openai import OpenAI
from .llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI API provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo", 
                 temperature: float = 0.3, max_tokens: int = 2000):
        super().__init__(model, temperature, max_tokens)
        
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not provided and not found in environment")
            
        self.client = OpenAI(api_key=api_key)
        
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using OpenAI"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {str(e)}")
            raise
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate JSON response using OpenAI"""
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
            logger.error(f"OpenAI JSON generation error: {str(e)}")
            raise
