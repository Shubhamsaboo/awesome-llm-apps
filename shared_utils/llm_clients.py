"""
LLM client factory and utilities.

Provides a unified interface for creating and managing LLM clients
across different providers (OpenAI, Anthropic, Google, etc.).
"""
from typing import Optional, Dict, Any
from enum import Enum
from .errors import ConfigurationError, ModelNotFoundError
from .config import get_env_var


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    COHERE = "cohere"
    OLLAMA = "ollama"


class LLMClientFactory:
    """Factory for creating LLM clients."""

    @staticmethod
    def create_client(
        provider: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Create an LLM client for the specified provider.

        Args:
            provider: Provider name (openai, anthropic, google, etc.)
            api_key: API key (if not provided, will try to load from env)
            **kwargs: Additional provider-specific arguments

        Returns:
            Configured LLM client

        Raises:
            ConfigurationError: If client cannot be created
            ModelNotFoundError: If provider is not supported
        """
        provider = provider.lower()

        try:
            if provider == "openai":
                return LLMClientFactory._create_openai_client(api_key, **kwargs)
            elif provider == "anthropic":
                return LLMClientFactory._create_anthropic_client(api_key, **kwargs)
            elif provider == "google":
                return LLMClientFactory._create_google_client(api_key, **kwargs)
            elif provider == "ollama":
                return LLMClientFactory._create_ollama_client(**kwargs)
            else:
                raise ModelNotFoundError(
                    f"Unsupported provider: {provider}",
                    details={"provider": provider}
                )
        except ImportError as e:
            raise ConfigurationError(
                f"Required library for {provider} not installed: {str(e)}",
                details={"provider": provider, "error": str(e)}
            )

    @staticmethod
    def _create_openai_client(api_key: Optional[str] = None, **kwargs) -> Any:
        """Create OpenAI client."""
        from openai import OpenAI

        if api_key is None:
            api_key = get_env_var("OPENAI_API_KEY", required=True)

        return OpenAI(api_key=api_key, **kwargs)

    @staticmethod
    def _create_anthropic_client(api_key: Optional[str] = None, **kwargs) -> Any:
        """Create Anthropic client."""
        from anthropic import Anthropic

        if api_key is None:
            api_key = get_env_var("ANTHROPIC_API_KEY", required=True)

        return Anthropic(api_key=api_key, **kwargs)

    @staticmethod
    def _create_google_client(api_key: Optional[str] = None, **kwargs) -> Any:
        """Create Google AI client."""
        import google.generativeai as genai

        if api_key is None:
            api_key = get_env_var("GOOGLE_API_KEY", required=True)

        genai.configure(api_key=api_key)
        return genai

    @staticmethod
    def _create_ollama_client(**kwargs) -> Any:
        """Create Ollama client."""
        from openai import OpenAI

        base_url = kwargs.get("base_url", "http://localhost:11434/v1")
        return OpenAI(base_url=base_url, api_key="ollama")


def get_llm_client(
    provider: str = "openai",
    api_key: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Convenience function to get an LLM client.

    Args:
        provider: Provider name
        api_key: API key
        **kwargs: Additional arguments

    Returns:
        Configured LLM client
    """
    return LLMClientFactory.create_client(provider, api_key, **kwargs)
