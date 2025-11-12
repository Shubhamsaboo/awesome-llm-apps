# Shared Utilities

Common utilities and helpers for all LLM applications in this repository.

## Overview

This package provides reusable components to reduce code duplication and improve consistency across all LLM apps.

## Modules

### `config.py` - Configuration Management
Handles environment variables, API keys, and configuration validation.

```python
from shared_utils import get_env_var, load_api_keys

# Get environment variable with validation
api_key = get_env_var("OPENAI_API_KEY", required=True, secret=True)

# Load all API keys
api_keys = load_api_keys()
```

### `errors.py` - Custom Exceptions
Provides a hierarchy of exceptions for consistent error handling.

```python
from shared_utils import LLMAppError, ConfigurationError, APIError

raise ConfigurationError("Missing API key", details={"key": "OPENAI_API_KEY"})
```

### `logging_config.py` - Logging Setup
Standardized logging configuration.

```python
from shared_utils import setup_logging, get_logger

# Set up logging
logger = setup_logging(name="my_app", level="INFO")

# Get logger
logger = get_logger(__name__)
logger.info("Application started")
```

### `llm_clients.py` - LLM Client Factory
Unified interface for creating LLM clients.

```python
from shared_utils import get_llm_client

# Create OpenAI client
client = get_llm_client("openai")

# Create Anthropic client
client = get_llm_client("anthropic")

# Create local Ollama client
client = get_llm_client("ollama", base_url="http://localhost:11434/v1")
```

## Installation

The shared utilities are part of the repository. To use them:

```python
# Add parent directory to path if needed
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared_utils import get_llm_client, setup_logging
```

## Best Practices

1. **Error Handling**: Use custom exceptions for better error tracking
2. **Logging**: Use the logging utilities for consistent log format
3. **Configuration**: Load all sensitive data from environment variables
4. **Type Hints**: All functions include type hints for better IDE support

## Examples

### Complete Application Setup

```python
from shared_utils import (
    setup_logging,
    get_llm_client,
    get_env_var,
    ConfigurationError
)

# Set up logging
logger = setup_logging(name="my_app", level="INFO")

try:
    # Get configuration
    model_name = get_env_var("MODEL_NAME", default="gpt-4")

    # Create LLM client
    client = get_llm_client("openai")

    logger.info(f"Application started with model: {model_name}")

except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    raise
```

## Contributing

When adding new utilities:
1. Add type hints to all functions
2. Include docstrings with examples
3. Add tests in the `tests/` directory
4. Update this README
