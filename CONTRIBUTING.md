# Contributing to Awesome LLM Apps

Thank you for your interest in contributing! This document provides guidelines and best practices.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Quality Standards](#code-quality-standards)
- [Security Guidelines](#security-guidelines)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a new branch for your feature/fix
4. Make your changes
5. Submit a pull request

## Development Setup

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Set Up Pre-commit Hooks

```bash
pre-commit install
```

This will automatically run:
- Code formatting (Black)
- Import sorting (isort)
- Linting (Ruff)
- Security scanning (Bandit)
- Type checking (mypy)

### Run Pre-commit Manually

```bash
pre-commit run --all-files
```

## Code Quality Standards

### Python Code Style

We follow PEP 8 with these specifics:
- Line length: 100 characters
- Use Black for formatting
- Use isort for import sorting
- Use Ruff for linting

### Type Hints

All new functions should include type hints:

```python
from typing import List, Optional, Dict

def process_data(
    items: List[str],
    config: Optional[Dict[str, str]] = None
) -> Dict[str, int]:
    \"\"\"Process data with configuration.\"\"\"
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    \"\"\"
    Short description of the function.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is invalid
    \"\"\"
    pass
```

### Error Handling

Use custom exceptions from `shared_utils.errors`:

```python
from shared_utils import ConfigurationError, ValidationError

if not api_key:
    raise ConfigurationError(
        "API key is required",
        details={"key_name": "OPENAI_API_KEY"}
    )
```

## Security Guidelines

### Critical Rules

1. **Never commit secrets**
   - Use environment variables for API keys
   - Never hardcode credentials
   - Add `.env` to `.gitignore`

2. **Avoid dangerous functions**
   - Never use `eval()` directly (use AST-based parsing)
   - Never use `shell=True` in subprocess calls
   - Never use `os.system()` for dynamic commands

3. **Validate all inputs**
   - Sanitize user inputs
   - Validate file paths
   - Check command arguments

### Security Checklist

Before submitting a PR, verify:
- [ ] No hardcoded API keys or secrets
- [ ] No use of `eval()`, `exec()`, or `__import__()`
- [ ] No `shell=True` in subprocess calls
- [ ] All user inputs are validated
- [ ] SQL queries use parameterization
- [ ] Error messages don't expose sensitive info

## Testing Requirements

### Test Coverage

- Minimum test coverage: 60%
- All new features must include tests
- All bug fixes must include regression tests

### Writing Tests

Create tests in the `tests/` directory:

```python
import pytest
from shared_utils import get_llm_client

@pytest.mark.unit
def test_get_llm_client_openai(mock_env_vars):
    \"\"\"Test OpenAI client creation.\"\"\"
    client = get_llm_client("openai")
    assert client is not None

@pytest.mark.security
def test_no_code_injection():
    \"\"\"Test that code injection is prevented.\"\"\"
    # Test security-critical functionality
    pass
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific markers
pytest -m unit
pytest -m security
pytest -m integration
```

### Test Markers

Use these markers to categorize tests:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.security` - Security tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.requires_api_key` - Tests requiring API keys

## Pull Request Process

### Before Submitting

1. **Run all checks locally**
   ```bash
   # Format code
   black .
   isort .

   # Run linter
   ruff check .

   # Run tests
   pytest

   # Run security scan
   bandit -r .
   ```

2. **Update documentation**
   - Update README if adding new features
   - Add docstrings to all functions
   - Update CHANGELOG if applicable

3. **Self-review your code**
   - Check for security issues
   - Verify test coverage
   - Review error handling

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Security fix
- [ ] Documentation update
- [ ] Code refactoring

## Testing
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Coverage maintained/improved

## Security
- [ ] No new security vulnerabilities
- [ ] Security scan passing
- [ ] Secrets not committed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. Automated checks must pass:
   - CI/CD pipeline
   - Security scans
   - Test coverage
   - Code quality checks

2. Code review by maintainers

3. Approval and merge

## Project Structure

```
awesome-llm-apps/
├── shared_utils/          # Shared utilities library
├── tests/                 # Test suite
├── starter_ai_agents/     # Starter agent examples
├── advanced_ai_agents/    # Advanced agent examples
├── rag_tutorials/         # RAG tutorials
├── .github/workflows/     # CI/CD workflows
├── requirements-dev.txt   # Development dependencies
├── pytest.ini            # Pytest configuration
└── pyproject.toml        # Project configuration
```

## Common Issues

### Import Errors

If you get import errors for `shared_utils`:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Pre-commit Failures

If pre-commit hooks fail:
```bash
# Fix formatting issues
black .
isort .

# Run pre-commit again
pre-commit run --all-files
```

### Test Failures

If tests fail with missing dependencies:
```bash
pip install -r requirements-dev.txt
```

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Tag issues appropriately (bug, enhancement, security, etc.)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
