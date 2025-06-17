import os
import time
import logging
import requests
from typing import Optional, List
from litellm import completion
from .config import QuizConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a constant for the GGUF model identifier
MISTRAL_GGUF_MODEL_ID = "mistral-7b-instruct-gguf (Local)"

class LLMManager:
    def __init__(self, config: Optional[QuizConfig] = None):
        self.config = config or QuizConfig()

    def get_current_model(self) -> str:
        """Returns the current model from the configuration."""
        return self.config.current_model

    def set_model(self, model_name: str):
        """Sets the current model in the configuration and determines the processing engine."""
        self.config.current_model = model_name
        logger.info(f"LLM model set to: {model_name}")

        if model_name == MISTRAL_GGUF_MODEL_ID:
            self.config.processing_engine = "llamacpp_gguf"
        # elif model_name in self.config.openai_models: # Assuming ContextGem might be used for OpenAI too
        #     self.config.processing_engine = "contextgem" 
        else: # Default to ContextGem for Ollama and potentially OpenAI models
            self.config.processing_engine = "contextgem"
        logger.info(f"Processing engine set to: {self.config.processing_engine}")

    def get_available_models(self) -> List[str]:
        """Returns a list of predefined Ollama models, OpenAI models, and the local GGUF model."""
        # Predefined list of Ollama models to offer in the UI
        predefined_ollama_models = [
            "llama3.3:8b",
            "mistral:7b", # This is the Ollama-served Mistral, distinct from local GGUF
            "qwen2.5:7b",
            "deepseek-coder:6.7b",
        ]
        openai_models_from_config = self.config.openai_models
        local_gguf_models = [MISTRAL_GGUF_MODEL_ID]
        
        # Combine all model sources and remove duplicates
        combined_models = list(set(predefined_ollama_models + openai_models_from_config + local_gguf_models))
        logger.info(f"Offering models in UI: {sorted(combined_models)}") # Log sorted list for consistency
        return sorted(combined_models) # Return sorted list

    def get_openai_models(self) -> List[str]:
        """Returns the list of OpenAI models from the configuration."""
        return self.config.openai_models

    def get_local_models(self) -> List[str]:
        """Retrieves a list of locally available Ollama models."""
        try:
            response = requests.get(f"{self.config.ollama_base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                return [model['name'] for model in models_data.get('models', [])]
            else:
                logger.error(f"Failed to get local models from Ollama: {response.status_code} - {response.text}")
                return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Ollama to get local models: {str(e)}")
            return []

    def _truncate_content(self, content: str, max_tokens: int = 3000) -> str:
        """Truncate content to fit within token limit."""
        try:
            import tiktoken # Moved import here to avoid error if not installed and method not used
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            tokens = encoding.encode(content)
            if len(tokens) > max_tokens:
                truncated_tokens = tokens[:max_tokens]
                return encoding.decode(truncated_tokens)
        except Exception as e:
            logger.warning(f"Token encoding/truncation failed, using character truncation: {str(e)}")
            # Fallback character truncation if tiktoken fails or is not available
            estimated_chars_per_token = 4 
            char_limit = max_tokens * estimated_chars_per_token
            if len(content) > char_limit:
                return content[:char_limit] + "..." # Add ellipsis if truncated
        return content

    def make_llm_request(self, prompt: str, max_tokens: int = 500, temperature: Optional[float] = None) -> Optional[str]:
        """Make LLM request with retry logic using litellm, using the currently configured model."""
        # Use structured output temperature for quiz generation
        if temperature is None:
            current_model = self.get_current_model()
            if current_model in self.config.openai_models:
                temperature = self.config.openai_structured_temperature
            else:
                temperature = self.config.structured_output_temperature
        
        current_model = self.get_current_model()
        openai_models_list = self.config.openai_models
        
        logger.info(f"Making LLM request with model: {current_model}, temperature: {temperature}")
        
        for attempt in range(self.config.max_retries):
            try:
                if current_model in openai_models_list:
                    logger.info(f"Using OpenAI API with model {current_model}")
                    response = completion(
                        model=current_model,
                        messages=[
                            {"role": "system", "content": "You are an expert quiz question generator. Always respond with valid JSON only, no additional text or markdown."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=max_tokens,
                        temperature=temperature,
                        response_format={"type": "json_object"} # Enforce JSON mode for OpenAI
                    )
                else: # Assuming Ollama model
                    logger.info(f"Using Ollama API with model {current_model}")
                    response = completion(
                        model=f"ollama/{current_model}", # Ensure "ollama/" prefix for LiteLLM
                        messages=[
                            {"role": "system", "content": "You are an expert quiz question generator. Always respond with valid JSON only, no additional text or markdown."},
                            {"role": "user", "content": prompt}
                        ],
                        api_base=self.config.ollama_base_url,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stream=False, # Ensure stream is False for non-streaming completion
                        response_format={"type": "json_object"} # Attempt to enforce JSON for Ollama too
                    )
                
                logger.info(f"LLM request successful with model {current_model}")
                return response.choices[0].message.content
                
            except RuntimeError as e:
                if "cannot schedule new futures after interpreter shutdown" in str(e):
                    logger.error("Interpreter shutdown detected - restart required")
                    return None # Cannot recover from this
                logger.error(f"RuntimeError in LLM request: {str(e)}", exc_info=True) # Log full traceback for RuntimeErrors
                # Do not raise here, let retry logic handle it or fail after retries
            except Exception as e:
                logger.warning(f"LLM request attempt {attempt + 1} for model {current_model} failed: {str(e)}")
                # Consider logging exc_info=True for more details on non-RuntimeError exceptions too if needed for debugging
            
            if attempt < self.config.max_retries - 1:
                sleep_duration = self.config.retry_delay * (2 ** attempt) # Exponential backoff
                logger.info(f"Retrying in {sleep_duration:.2f} seconds...")
                time.sleep(sleep_duration)
            else:
                logger.error(f"All {self.config.max_retries} attempts failed for model {current_model}")
                    
        return None

    def test_ollama_connection(self) -> bool:
        """Test connection to Ollama server with retries using the current model."""
        current_model_to_test = self.get_current_model()
        
        # If current model is OpenAI or the GGUF model, test generic Ollama server reachability
        if current_model_to_test in self.config.openai_models or current_model_to_test == MISTRAL_GGUF_MODEL_ID:
            logger.info(f"Current model is '{current_model_to_test}'. Testing generic Ollama server reachability at {self.config.ollama_base_url}.")
            try:
                response = requests.get(self.config.ollama_base_url, timeout=5)
                response.raise_for_status() # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
                logger.info(f"Successfully connected to Ollama base URL: {self.config.ollama_base_url}")
                # Additionally, check if /api/tags is responsive as a basic health check
                tags_response = requests.get(f"{self.config.ollama_base_url}/api/tags", timeout=5)
                tags_response.raise_for_status()
                logger.info("Ollama /api/tags endpoint is responsive.")
                return True
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to connect to Ollama base URL ({self.config.ollama_base_url}) or /api/tags: {str(e)}")
                return False

        # If it's an Ollama model (not GGUF), test with the specific model
        logger.info(f"Testing Ollama connection with specific model: {current_model_to_test}")
        for attempt in range(self.config.max_retries):
            try:
                # Use a very short prompt for testing
                response = completion(
                    model=f"ollama/{current_model_to_test}",
                    messages=[{"role": "user", "content": "Hi"}],
                    api_base=self.config.ollama_base_url,
                    max_tokens=5,
                    temperature=0.1
                )
                logger.info(f"Successfully connected to Ollama and got response from model {current_model_to_test}")
                return True
            except Exception as e:
                logger.warning(f"Ollama connection attempt {attempt + 1} with model {current_model_to_test} failed: {str(e)}")
                if "model not found" in str(e).lower() or "pull model" in str(e).lower():
                    logger.error(f"Model '{current_model_to_test}' not found on Ollama server. Please pull it first using 'ollama pull {current_model_to_test}'.")
                    return False # No point retrying if model is not there
                if attempt < self.config.max_retries - 1:
                    sleep_duration = self.config.retry_delay * (2 ** attempt) # Exponential backoff
                    logger.info(f"Retrying Ollama connection in {sleep_duration:.2f} seconds...")
                    time.sleep(sleep_duration)
                    
        logger.error(f"Failed to connect to Ollama with model {current_model_to_test} after all {self.config.max_retries} retries.")
        return False

    def is_model_available(self, model_name: str) -> bool:
        """Check if a specific Ollama model is available locally."""
        if model_name == MISTRAL_GGUF_MODEL_ID: # GGUF model availability is checked by file existence
             gguf_path = self.config.gguf_model_path if self.config else "./mistral-7b-instruct-v0.1.Q8_0.gguf"
             return os.path.exists(gguf_path)

        try:
            local_ollama_models = self.get_local_models()
            # Ollama model names can be like 'mistral:latest' or just 'mistral'.
            # We need to check if the base name matches.
            base_model_name = model_name.split(':')[0]
            for local_model in local_ollama_models:
                if local_model.split(':')[0] == base_model_name:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking Ollama model availability for {model_name}: {e}")
            return False # Assume not available if error occurs

    def pull_model(self, model_name: str) -> bool:
        """Pull an Ollama model from its registry."""
        if model_name == MISTRAL_GGUF_MODEL_ID:
            logger.info(f"Model '{model_name}' is a local GGUF model. Pulling is handled by 'download_gguf_model.py'.")
            return self.is_model_available(model_name) # Check if file exists

        logger.info(f"Attempting to pull Ollama model: {model_name}...")
        stream = None
        try:
            # Using requests directly for more control over streaming and timeout
            response = requests.post(
                f"{self.config.ollama_base_url}/api/pull",
                json={"name": model_name, "stream": False}, # stream: False to wait for completion
                timeout=self.config.pull_timeout # Long timeout for model download
            )
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            # If stream=False, response.text might contain final status or be empty on success
            # The main indicator is the 200 OK status.
            logger.info(f"Ollama pull request for '{model_name}' completed with status {response.status_code}.")
            
            # Verify model is now listed
            time.sleep(2) # Give Ollama a moment to update its tags
            if self.is_model_available(model_name):
                logger.info(f"Successfully pulled and verified model '{model_name}'.")
                return True
            else:
                logger.error(f"Model '{model_name}' pull request sent, but model not found in local list after pull. Response: {response.text[:500]}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout occurred while pulling model '{model_name}' (timeout: {self.config.pull_timeout}s).")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error pulling Ollama model '{model_name}': {str(e)}")
            return False
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"An unexpected error occurred during pull_model for '{model_name}': {str(e)}", exc_info=True)
            return False
        finally:
            if stream: # Ensure response is closed if stream=True was used (not current case)
                try:
                    stream.close()
                except Exception:
                    pass
