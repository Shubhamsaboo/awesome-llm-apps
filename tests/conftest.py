"""
Pytest configuration and shared fixtures for all tests.

This file contains fixtures and configuration that can be used
across all test files in the test suite.
"""
import os
import pytest
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, MagicMock


# Configure test environment
os.environ["TESTING"] = "true"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing without API calls."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    test_vars = {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "GOOGLE_API_KEY": "test-google-key",
    }
    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)
    return test_vars


@pytest.fixture
def sample_text():
    """Provide sample text for testing."""
    return "This is a sample text for testing purposes."


@pytest.fixture
def sample_pdf_path(temp_dir) -> Path:
    """Create a sample PDF file for testing."""
    pdf_path = temp_dir / "sample.pdf"
    # Create a minimal PDF for testing
    # In real tests, you would use a library like reportlab or PyPDF2
    pdf_path.write_text("Sample PDF content")
    return pdf_path


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment after each test."""
    yield
    # Cleanup code here if needed


# Markers for skipping tests based on conditions
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "requires_api_key: mark test as requiring external API keys"
    )
    config.addinivalue_line(
        "markers", "requires_ollama: mark test as requiring local Ollama"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers and environment."""
    skip_api = pytest.mark.skip(reason="API keys not available")
    skip_ollama = pytest.mark.skip(reason="Ollama not available")

    for item in items:
        # Skip tests requiring API keys if not in environment
        if "requires_api_key" in item.keywords:
            if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY", "").startswith("test-"):
                item.add_marker(skip_api)

        # Skip tests requiring Ollama if not available
        if "requires_ollama" in item.keywords:
            # You could add a check here to see if Ollama is running
            pass
