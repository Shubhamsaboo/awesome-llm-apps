# 🤝 Contributing to Awesome LLM Apps

Thank you for your interest in contributing to Awesome LLM Apps! This document provides guidelines and best practices for contributing to this project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## 📜 Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful and constructive in all interactions.

### Our Standards

- **Be Respectful**: Treat everyone with respect and kindness
- **Be Collaborative**: Work together to achieve common goals
- **Be Professional**: Maintain professional conduct in all communications
- **Be Inclusive**: Welcome and support people of all backgrounds

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.8 or higher
- Git
- pip or conda for package management

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/awesome-llm-apps.git
   cd awesome-llm-apps
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/Shubhamsaboo/awesome-llm-apps.git
   ```

## 💻 Development Setup

### 1. Create a Virtual Environment

```bash
# Using venv
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install project dependencies
pip install -r requirements.txt

# For development dependencies
pip install -r requirements-dev.txt  # if available
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
# Add other required API keys
```

## 🛠️ How to Contribute

### Types of Contributions

We welcome various types of contributions:

1. **Bug Fixes**: Fix existing issues
2. **New Features**: Add new AI agents or applications
3. **Documentation**: Improve or add documentation
4. **Tests**: Add or improve test coverage
5. **Performance**: Optimize existing code
6. **Examples**: Add usage examples

### Creating a New AI Agent

When adding a new AI agent, follow this structure:

```
awesome-llm-apps/
├── [category]_ai_agents/
│   └── your_agent_name/
│       ├── README.md
│       ├── requirements.txt
│       ├── your_agent.py
│       ├── .env.example
│       └── assets/ (if needed)
```

#### README Template for New Agents

```markdown
# Your Agent Name 🤖

Brief description of what your agent does.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

\`\`\`bash
pip install -r requirements.txt
\`\`\`

## Configuration

1. Copy `.env.example` to `.env`
2. Add your API keys

## Usage

\`\`\`bash
python your_agent.py
\`\`\`

## Example

[Provide a concrete example]

## Requirements

- Python 3.8+
- API keys required
- Other dependencies
```

## 📝 Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

```python
# Good: Clear, descriptive names
def process_legal_document(file_path: str) -> dict:
    """
    Process a legal document and extract key information.
    
    Args:
        file_path: Path to the legal document
        
    Returns:
        Dictionary containing extracted information
    """
    pass

# Bad: Unclear names, no type hints
def proc(f):
    pass
```

### Import Organization

```python
# Standard library imports
import os
import sys
from typing import List, Dict

# Third-party imports
import streamlit as st
import pandas as pd

# Local imports
from agno.agent import Agent
from agno.models.openai import OpenAIChat
```

### Error Handling

Always include proper error handling:

```python
try:
    result = agent.run(query)
    st.success("✅ Operation completed successfully!")
except ValueError as e:
    st.error(f"❌ Invalid input: {str(e)}")
except Exception as e:
    st.error(f"❌ An error occurred: {str(e)}")
    # Log the error for debugging
    logger.error(f"Error in agent execution: {str(e)}", exc_info=True)
```

### Documentation

- **Docstrings**: Use Google-style docstrings
- **Comments**: Explain why, not what
- **Type Hints**: Use type hints for function parameters and return values

```python
def create_agent(
    name: str,
    model: str,
    tools: List[str] = None
) -> Agent:
    """
    Create a new AI agent with specified configuration.
    
    Args:
        name: Name of the agent
        model: Model identifier (e.g., 'gpt-4o')
        tools: Optional list of tool names
        
    Returns:
        Configured Agent instance
        
    Raises:
        ValueError: If model is not supported
    """
    pass
```

## 🧪 Testing Guidelines

### Writing Tests

Create tests for new features:

```python
import pytest
from your_agent import process_document

def test_process_document_success():
    """Test successful document processing"""
    result = process_document("test.pdf")
    assert result is not None
    assert "content" in result

def test_process_document_invalid_file():
    """Test handling of invalid file"""
    with pytest.raises(ValueError):
        process_document("nonexistent.pdf")
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_your_agent.py

# Run with coverage
pytest --cov=your_agent tests/
```

## 🔄 Pull Request Process

### 1. Create a Branch

```bash
# Update your fork
git fetch upstream
git checkout main
git merge upstream/main

# Create a feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clean, documented code
- Follow coding standards
- Add tests if applicable
- Update documentation

### 3. Commit Your Changes

Use clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: Add AI legal document analyzer

- Implement document processing
- Add multi-agent coordination
- Include error handling
- Update documentation"
```

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

### 4. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:

- **Clear title**: Summarize the change
- **Description**: Explain what and why
- **Screenshots**: If UI changes
- **Testing**: How you tested it
- **Related Issues**: Link to related issues

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
How has this been tested?

## Screenshots (if applicable)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added/updated
```

## 🐛 Reporting Bugs

### Before Submitting

1. **Check existing issues**: Search for similar bugs
2. **Try latest version**: Ensure you're using the latest code
3. **Minimal reproduction**: Create a minimal example

### Bug Report Template

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Windows 11]
- Python Version: [e.g., 3.10.5]
- Package Version: [e.g., agno 0.1.0]

## Additional Context
Screenshots, logs, etc.
```

## 💡 Suggesting Enhancements

### Enhancement Template

```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed?

## Proposed Solution
How would you implement it?

## Alternatives Considered
Other approaches you've thought about

## Additional Context
Mockups, examples, etc.
```

## 🎨 UI/UX Guidelines

When creating Streamlit apps:

### Layout Best Practices

```python
# Use columns for better layout
col1, col2 = st.columns(2)
with col1:
    st.metric("Metric 1", "Value 1")
with col2:
    st.metric("Metric 2", "Value 2")

# Use expanders for optional content
with st.expander("Advanced Options"):
    option = st.selectbox("Choose option", ["A", "B", "C"])

# Use tabs for organized content
tab1, tab2, tab3 = st.tabs(["Analysis", "Results", "Settings"])
```

### Visual Consistency

- **Icons**: Use consistent emoji icons
- **Colors**: Follow a consistent color scheme
- **Spacing**: Use `st.divider()` for visual separation
- **Feedback**: Always provide user feedback (success, error, info)

### Error Messages

```python
# Good: Helpful error message
st.error("❌ Failed to load document. Please ensure the file is a valid PDF and try again.")

# Bad: Unclear error message
st.error("Error")
```

## 📚 Documentation Guidelines

### README Structure

Every agent should have a comprehensive README:

1. **Title and Description**
2. **Features**
3. **Installation**
4. **Configuration**
5. **Usage**
6. **Examples**
7. **Troubleshooting**
8. **Contributing**
9. **License**

### Code Comments

```python
# Good: Explains why
# Using exponential backoff to handle rate limits
retry_with_backoff(api_call)

# Bad: Explains what (obvious from code)
# Call the API
api_call()
```

## 🔍 Code Review Process

### What Reviewers Look For

1. **Functionality**: Does it work as intended?
2. **Code Quality**: Is it clean and maintainable?
3. **Testing**: Are there adequate tests?
4. **Documentation**: Is it well documented?
5. **Performance**: Are there any performance issues?
6. **Security**: Are there security concerns?

### Responding to Reviews

- **Be receptive**: Welcome feedback
- **Ask questions**: If unclear, ask for clarification
- **Make changes**: Address all comments
- **Explain decisions**: If you disagree, explain why

## 🏆 Recognition

Contributors will be recognized in:

- README.md contributors section
- Release notes
- Project documentation

## 📞 Getting Help

- **GitHub Issues**: For bugs and features
- **Discussions**: For questions and ideas
- **Discord/Slack**: For real-time chat (if available)

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Awesome LLM Apps! 🎉

Your contributions help make AI more accessible to everyone.
