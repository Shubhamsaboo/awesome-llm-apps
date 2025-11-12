"""
Custom exception classes for LLM applications.

This module provides a hierarchy of exceptions that can be used
across all LLM apps for consistent error handling.
"""


class LLMAppError(Exception):
    """Base exception for all LLM app errors."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(LLMAppError):
    """Raised when there's a configuration error."""

    pass


class APIError(LLMAppError):
    """Raised when an API call fails."""

    def __init__(self, message: str, status_code: int = None, details: dict = None):
        self.status_code = status_code
        super().__init__(message, details)

    def __str__(self):
        base_msg = super().__str__()
        if self.status_code:
            return f"{base_msg} | Status Code: {self.status_code}"
        return base_msg


class ValidationError(LLMAppError):
    """Raised when input validation fails."""

    pass


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""

    pass


class AuthenticationError(APIError):
    """Raised when API authentication fails."""

    pass


class ModelNotFoundError(LLMAppError):
    """Raised when requested model is not found."""

    pass


class TokenLimitError(LLMAppError):
    """Raised when token limit is exceeded."""

    pass
