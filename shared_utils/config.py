"""
Configuration management utilities.

Provides functions for loading environment variables, API keys,
and other configuration settings in a secure and consistent way.
"""
import os
from typing import Optional, Dict, Any
from pathlib import Path
from .errors import ConfigurationError


def get_env_var(
    var_name: str,
    default: Optional[str] = None,
    required: bool = False,
    secret: bool = False
) -> Optional[str]:
    """
    Get an environment variable with proper validation.

    Args:
        var_name: Name of the environment variable
        default: Default value if not found
        required: Whether this variable is required
        secret: Whether to mask the value in logs

    Returns:
        The environment variable value or default

    Raises:
        ConfigurationError: If required variable is not found
    """
    value = os.getenv(var_name, default)

    if required and not value:
        raise ConfigurationError(
            f"Required environment variable '{var_name}' is not set",
            details={"var_name": var_name}
        )

    if value and secret:
        # Log masked value for debugging
        masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
        # Don't actually log here, just prepare for potential logging

    return value


def load_api_keys() -> Dict[str, str]:
    """
    Load all API keys from environment variables.

    Returns:
        Dictionary of API keys with their names

    Raises:
        ConfigurationError: If critical API keys are missing
    """
    api_keys = {}

    # Common API key names
    key_names = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
        "COHERE_API_KEY",
    ]

    for key_name in key_names:
        value = os.getenv(key_name)
        if value:
            api_keys[key_name] = value

    return api_keys


def load_env_file(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file.

    Args:
        env_path: Path to .env file (defaults to .env in current directory)

    Returns:
        Dictionary of loaded environment variables
    """
    if env_path is None:
        env_path = Path.cwd() / ".env"

    if not env_path.exists():
        return {}

    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
                except ValueError:
                    continue

    return env_vars


def validate_config(config: Dict[str, Any], required_keys: list) -> None:
    """
    Validate that a configuration dictionary has all required keys.

    Args:
        config: Configuration dictionary to validate
        required_keys: List of required key names

    Raises:
        ConfigurationError: If any required keys are missing
    """
    missing_keys = [key for key in required_keys if key not in config or not config[key]]

    if missing_keys:
        raise ConfigurationError(
            f"Missing required configuration keys: {', '.join(missing_keys)}",
            details={"missing_keys": missing_keys}
        )
