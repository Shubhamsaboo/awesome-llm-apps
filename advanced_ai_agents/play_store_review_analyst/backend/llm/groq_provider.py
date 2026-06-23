import json
import logging
import os
import time
from typing import Optional, Dict, Any
from groq import Groq, RateLimitError, APIError
from .llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """Groq API provider - Ultra-fast inference engine"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile", 
                 temperature: float = 0.3, max_tokens: int = 8000):
        """
        Initialize Groq provider.
        
        Available models:
        - llama-3.3-70b-versatile (Recommended - Best for general tasks)
        - llama-3.3-70b-specdec (Speculative decoding - faster)
        - llama-3.1-8b-instant (Fastest - good for simple tasks)
        - mixtral-8x7b-32768 (Good context window)
        - gemma2-9b-it (Google's Gemma)
        """
        super().__init__(model, temperature, max_tokens)
        
        api_key = api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not provided and not found in environment")
            
        self.client = Groq(api_key=api_key)
        logger.info(f"Initialized Groq provider with model: {model}")
        
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using Groq"""
        max_retries = 3
        retry_delay = 10  # Groq is fast, shorter retry delay

        for attempt in range(max_retries):
            try:
                logger.info(f"🤖 Calling Groq API ({self.model})... (attempt {attempt + 1}/{max_retries})")
                logger.debug(f"Prompt length: {len(prompt)} chars")

                # Prepare messages
                messages = []
                
                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
                    })
                
                messages.append({
                    "role": "user",
                    "content": prompt
                })

                # Call Groq API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )

                # Extract text from response
                response_text = response.choices[0].message.content

                # Log the call
                self.log_call(len(prompt), len(response_text))

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
            except APIError as e:
                logger.error(f"❌ Groq API error: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"❌ Groq generation error: {str(e)}")
                raise
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate JSON response using Groq"""
        max_retries = 3
        retry_delay = 10

        for attempt in range(max_retries):
            try:
                # Add JSON mode instruction
                json_system_prompt = "You are a helpful assistant that responds only in valid JSON format. Never use markdown code blocks."
                if system_prompt:
                    json_system_prompt = f"{system_prompt}\n\n{json_system_prompt}"
                
                json_prompt = f"{prompt}\n\nRespond ONLY with valid JSON, no markdown formatting or code blocks."
                
                # Try using Groq's JSON mode if available (some models support it)
                try:
                    messages = []
                    if json_system_prompt:
                        messages.append({"role": "system", "content": json_system_prompt})
                    messages.append({"role": "user", "content": json_prompt})
                    
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        response_format={"type": "json_object"}  # Force JSON output
                    )
                    
                    response_text = response.choices[0].message.content
                    
                except Exception as json_mode_error:
                    # Fallback to regular generation if JSON mode not supported
                    logger.debug(f"JSON mode not supported, falling back to regular mode: {json_mode_error}")
                    response_text = self.generate(json_prompt, json_system_prompt)

                # Clean up the response
                response_text = response_text.strip()

                # Remove markdown code blocks if present
                if "```" in response_text:
                    parts = response_text.split("```")
                    for i, part in enumerate(parts):
                        if i % 2 == 1:  # Odd indices are inside code blocks
                            if part.startswith("json"):
                                response_text = part[4:].strip()
                            else:
                                response_text = part.strip()
                            break

                # Try to fix incomplete JSON
                if not response_text.endswith((']', '}')):
                    logger.warning("Response appears incomplete, attempting to fix...")
                    last_bracket = response_text.rfind(']')
                    last_brace = response_text.rfind('}')
                    if last_bracket > 0 or last_brace > 0:
                        end_pos = max(last_bracket, last_brace) + 1
                        response_text = response_text[:end_pos]

                parsed = json.loads(response_text)
                
                # Log the call
                self.log_call(len(prompt), len(response_text))
                
                return parsed

            except RateLimitError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Rate limit exceeded during JSON generation (attempt {attempt + 1}/{max_retries}). Waiting {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"❌ Rate limit exceeded after {max_retries} attempts: {str(e)}")
                    raise
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                logger.error(f"Response: {response_text[:500] if 'response_text' in locals() else 'N/A'}")
                # Return empty list/dict as fallback
                return [] if prompt.strip().endswith("array") or "[" in response_text[:50] else {}
            except Exception as e:
                logger.error(f"Groq JSON generation error: {str(e)}")
                raise