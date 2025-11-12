"""
Shared utilities for awesome-llm-apps.

This package contains common utilities, helpers, and patterns
used across multiple LLM applications in this repository.
"""

__version__ = "1.0.0"

from .config import get_env_var, load_api_keys
from .errors import (
    LLMAppError,
    ConfigurationError,
    APIError,
    ValidationError,
)
from .llm_clients import get_llm_client, LLMClientFactory
from .logging_config import setup_logging, get_logger

__all__ = [
    # Configuration
    "get_env_var",
    "load_api_keys",
    # Errors
    "LLMAppError",
    "ConfigurationError",
    "APIError",
    "ValidationError",
    # LLM Clients
    "get_llm_client",
    "LLMClientFactory",
    # Logging
    "setup_logging",
    "get_logger",
]
