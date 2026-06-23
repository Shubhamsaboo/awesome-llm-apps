import json
import logging
import os
import time
from typing import Optional, Dict, Any
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from .llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini API provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash", 
                 temperature: float = 0.3, max_tokens: int = 8000):
        super().__init__(model, temperature, max_tokens)
        
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not provided and not found in environment")
            
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)
        
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using Gemini"""
        max_retries = 3
        retry_delay = 45  # seconds

        for attempt in range(max_retries):
            try:
                full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

                logger.info(f"🤖 Calling Gemini API ({self.model})... (attempt {attempt + 1}/{max_retries})")
                logger.debug(f"Prompt length: {len(full_prompt)} chars")

                response = self.client.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.temperature,
                        max_output_tokens=self.max_tokens,
                    ),
                )

                response_text = response.text

                # Log the call
                self.log_call(len(full_prompt), len(response_text))

                logger.info(f"✓ Received response ({len(response_text)} chars)")
                logger.debug(f"Response preview: {response_text[:200]}...")

                return response_text

            except google_exceptions.ResourceExhausted as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Quota limit exceeded (attempt {attempt + 1}/{max_retries}). Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"❌ Quota limit exceeded after {max_retries} attempts: {str(e)}")
                    raise
            except Exception as e:
                logger.error(f"❌ Gemini generation error: {str(e)}")
                raise
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate JSON response using Gemini"""
        max_retries = 3
        retry_delay = 45  # seconds

        for attempt in range(max_retries):
            try:
                json_prompt = f"{prompt}\n\nRespond ONLY with valid JSON, no markdown formatting."
                response_text = self.generate(json_prompt, system_prompt)

                # Clean up the response
                original_response = response_text
                response_text = response_text.strip()

                # Remove markdown code blocks if present
                if "```" in response_text:
                    # Extract content between code blocks
                    parts = response_text.split("```")
                    for i, part in enumerate(parts):
                        if i % 2 == 1:  # Odd indices are inside code blocks
                            if part.startswith("json"):
                                response_text = part[4:].strip()
                            else:
                                response_text = part.strip()
                            break

                # Try to fix incomplete JSON by finding the last complete object/array
                if not response_text.endswith((']', '}')):
                    logger.warning("Response appears incomplete, attempting to fix...")
                    # Try to find the last complete array
                    last_bracket = response_text.rfind(']')
                    last_brace = response_text.rfind('}')
                    if last_bracket > 0 or last_brace > 0:
                        end_pos = max(last_bracket, last_brace) + 1
                        response_text = response_text[:end_pos]

                parsed = json.loads(response_text)
                return parsed

            except google_exceptions.ResourceExhausted as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Quota limit exceeded during JSON generation (attempt {attempt + 1}/{max_retries}). Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"❌ Quota limit exceeded after {max_retries} attempts during JSON generation: {str(e)}")
                    raise
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}, response: {response_text[:500] if 'response_text' in locals() else 'N/A'}")
                # Return empty list/dict as fallback
                return [] if prompt.strip().endswith("array") or "[" in response_text[:50] else {}
            except Exception as e:
                logger.error(f"Gemini JSON generation error: {str(e)}")
                raise
