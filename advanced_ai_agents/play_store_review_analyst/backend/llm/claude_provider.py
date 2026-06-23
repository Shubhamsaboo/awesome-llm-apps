import json
import logging
import os
import time
from typing import Optional, Dict, Any
try:
    from anthropic import Anthropic
    from anthropic import APIError, RateLimitError, APIStatusError
except ImportError:
    raise ImportError("Please install anthropic: pip install anthropic")

from .llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class ClaudeProvider(LLMProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514", 
                 temperature: float = 0.3, max_tokens: int = 8000):
        super().__init__(model, temperature, max_tokens)
        
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not provided and not found in environment")
        
        # Initialize client with only the api_key parameter
        try:
            self.client = Anthropic(api_key=api_key)
            logger.info(f"✓ Claude client initialized successfully with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {str(e)}")
            raise
        
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using Claude"""
        max_retries = 3
        retry_delay = 45  # seconds

        for attempt in range(max_retries):
            try:
                logger.info(f"🤖 Calling Claude API ({self.model})... (attempt {attempt + 1}/{max_retries})")
                logger.debug(f"Prompt length: {len(prompt)} chars")

                # Prepare messages
                messages = [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]

                # Prepare kwargs for API call
                api_kwargs = {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "messages": messages
                }
                
                # Only add system prompt if provided
                if system_prompt:
                    api_kwargs["system"] = system_prompt

                # Call Claude API
                response = self.client.messages.create(**api_kwargs)

                # Extract text from response
                response_text = ""
                for block in response.content:
                    if hasattr(block, 'type') and block.type == "text":
                        response_text += block.text

                # Log the call
                self.log_call(len(prompt) + (len(system_prompt) if system_prompt else 0), len(response_text))

                logger.info(f"✓ Received response ({len(response_text)} chars)")
                logger.debug(f"Response preview: {response_text[:200]}...")

                return response_text

            except RateLimitError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Rate limit exceeded (attempt {attempt + 1}/{max_retries}). Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"❌ Rate limit exceeded after {max_retries} attempts: {str(e)}")
                    raise
            except APIStatusError as e:
                logger.error(f"❌ Claude API status error: {e.status_code} - {str(e)}")
                raise
            except APIError as e:
                logger.error(f"❌ Claude API error: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"❌ Claude generation error: {str(e)}", exc_info=True)
                raise
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate JSON response using Claude"""
        max_retries = 3
        retry_delay = 45  # seconds

        for attempt in range(max_retries):
            try:
                json_prompt = f"{prompt}\n\nIMPORTANT: Respond ONLY with valid JSON. Do not include any markdown formatting, code blocks, or explanatory text. Just raw JSON."
                response_text = self.generate(json_prompt, system_prompt)

                # Clean up the response
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
                    last_bracket = response_text.rfind(']')
                    last_brace = response_text.rfind('}')
                    if last_bracket > 0 or last_brace > 0:
                        end_pos = max(last_bracket, last_brace) + 1
                        response_text = response_text[:end_pos]

                # Parse JSON
                parsed = json.loads(response_text)
                logger.debug(f"Successfully parsed JSON response")
                return parsed

            except RateLimitError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Rate limit exceeded during JSON generation (attempt {attempt + 1}/{max_retries}). Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"❌ Rate limit exceeded after {max_retries} attempts during JSON generation: {str(e)}")
                    raise
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                logger.error(f"Response was: {response_text[:500] if 'response_text' in locals() else 'N/A'}")
                # Return empty list/dict as fallback
                if "[" in (prompt + response_text)[:100]:
                    logger.warning("Returning empty list as fallback")
                    return []
                else:
                    logger.warning("Returning empty dict as fallback")
                    return {}
            except Exception as e:
                logger.error(f"Claude JSON generation error: {str(e)}", exc_info=True)
                raise