# Contributing to Awesome LLM Apps

Thank you for your interest in contributing to Awesome LLM Apps! This repository is a community-driven collection of LLM applications, and we welcome contributions from developers of all experience levels.

## Table of Contents

- [Quick Start for Contributors](#quick-start-for-contributors)
- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [First-Time Contributors](#first-time-contributors)
- [Submitting a New LLM App](#submitting-a-new-llm-app)
- [Project Requirements](#project-requirements)
- [Documentation Guidelines](#documentation-guidelines)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Review Criteria](#review-criteria)
- [Getting Help](#getting-help)

## Quick Start for Contributors

**Ready to contribute? Here's the fastest path:**

1. **Fork & Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/awesome-llm-apps.git
   cd awesome-llm-apps
   ```

2. **Create a Branch**
   ```bash
   git checkout -b add-your-app-name
   ```

3. **Add Your App** (see [Project Structure](#step-2-create-your-project-structure) below)

4. **Test Locally**
   ```bash
   cd your_category/your_app_name
   pip install -r requirements.txt
   python your_main_script.py  # or streamlit run your_main_script.py
   ```

5. **Submit PR** with a clear title: `Add [App Name]: Brief description`

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. By participating in this project, you agree to:

- Be respectful and considerate in all interactions
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Accept responsibility for mistakes and learn from them

## Ways to Contribute

| Contribution Type | Description | Difficulty |
|-------------------|-------------|------------|
| **Add a new LLM app** | Submit your own LLM-powered application | Varies |
| **Improve existing apps** | Fix bugs, improve documentation, or enhance features | 🟢 Easy |
| **Report issues** | Help identify bugs or suggest improvements | 🟢 Easy |
| **Review pull requests** | Help review and test contributions from others | 🟡 Medium |
| **Improve documentation** | Fix typos, clarify instructions, add examples | 🟢 Easy |

## First-Time Contributors

**New to open source? Welcome!** Here are some beginner-friendly ways to start:

### Good First Issues

Look for issues labeled:
- `good first issue` - Simple, well-defined tasks
- `documentation` - Documentation improvements
- `bug` - Bug fixes in existing apps

### Beginner-Friendly Contributions

1. **Fix typos or improve documentation** in existing README files
2. **Add missing requirements** to existing `requirements.txt` files
3. **Improve error messages** in existing apps
4. **Add example prompts** to app documentation
5. **Create a local variant** of an existing cloud-only app

### Setting Up Your Development Environment

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/awesome-llm-apps.git
cd awesome-llm-apps

# 3. Add the upstream remote
git remote add upstream https://github.com/Shubhamsaboo/awesome-llm-apps.git

# 4. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 5. Keep your fork updated
git fetch upstream
git merge upstream/main
```

## Submitting a New LLM App

### Step 1: Choose the Right Category

Select the most appropriate category for your app based on complexity and type:

| Category | Directory | Description | Level |
|----------|-----------|-------------|-------|
| Starter AI Agents | `starter_ai_agents/` | Beginner-friendly, single-purpose agents | 🟢 |
| Advanced Single Agents | `advanced_ai_agents/single_agent_apps/` | Complex single-agent implementations | 🟡 |
| Multi-Agent Apps | `advanced_ai_agents/multi_agent_apps/` | Apps with multiple collaborating agents | 🟡 |
| Agent Teams | `advanced_ai_agents/multi_agent_apps/agent_teams/` | Specialized multi-agent team systems | 🔴 |
| Game Playing Agents | `advanced_ai_agents/autonomous_game_playing_agent_apps/` | Autonomous game-playing AI | 🟡 |
| Voice AI Agents | `voice_ai_agents/` | Voice-enabled AI applications | 🟡 |
| MCP AI Agents | `mcp_ai_agents/` | Model Context Protocol agents | 🔴 |
| RAG Tutorials | `rag_tutorials/` | Retrieval-Augmented Generation apps | 🟢-🟡 |
| Memory Tutorials | `advanced_llm_apps/llm_apps_with_memory_tutorials/` | Apps demonstrating memory patterns | 🟡 |
| Chat with X | `advanced_llm_apps/chat_with_X_tutorials/` | Conversational interfaces for various data sources | 🟢-🟡 |
| Optimization Tools | `advanced_llm_apps/llm_optimization_tools/` | LLM optimization utilities | 🟡-🔴 |
| Fine-tuning | `advanced_llm_apps/llm_finetuning_tutorials/` | Model fine-tuning tutorials | 🔴 |

**Complexity Levels:**
- 🟢 **Beginner**: 5-15 min setup, single API key, minimal dependencies
- 🟡 **Intermediate**: 15-30 min setup, multiple components, some configuration
- 🔴 **Advanced**: 30-60+ min setup, complex architecture, significant configuration

### Step 2: Create Your Project Structure

Your project should follow this structure:

```
your_project_name/
├── README.md              # Required: Project documentation
├── requirements.txt       # Required: Python dependencies
├── main_script.py         # Required: Main application file
├── local_variant.py       # Optional: Local LLM version (Ollama, etc.)
├── agent.py               # Optional: Agent definitions (for multi-agent)
├── tools.py               # Optional: Custom tools
└── outputs/               # Optional: Generated artifacts
```

**Naming conventions:**
- Use lowercase with underscores for directory names (e.g., `ai_travel_agent`)
- Use descriptive names that reflect the app's purpose
- Prefix with `ai_` for AI agent apps

## Project Requirements

### Must Have ✅

- [ ] **Working code**: Your app must be functional and runnable
- [ ] **README.md**: Comprehensive documentation (see template below)
- [ ] **requirements.txt**: All Python dependencies with versions
- [ ] **Main script**: Entry point for running the application
- [ ] **Clear purpose**: The app should demonstrate a specific LLM use case

### Should Have 📋

- [ ] **API key instructions**: Clear guidance on obtaining required API keys
- [ ] **Error handling**: Graceful handling of common errors
- [ ] **Local variant**: Option to run with local models when applicable

### Nice to Have ⭐

- [ ] **Architecture explanation**: How the app works internally
- [ ] **Example prompts**: Sample inputs for users to try
- [ ] **Tutorial link**: Link to a detailed walkthrough article

## Documentation Guidelines

### README.md Template

Use this template for your project's README:

```markdown
## [Emoji] [Project Title]

Brief description of what your app does and its key value proposition.

### Features

- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/[category]/[your_project_name]
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Get your API Keys

- [Provider Name]: Sign up at [URL] and obtain your API key
- [Other Provider]: Sign up at [URL] and obtain your API key

4. Run the application

```bash
streamlit run your_main_script.py
# or
python your_main_script.py
```

### How it Works?

Explain the architecture and key components of your application.

- **Component 1**: What it does
- **Component 2**: What it does

### Configuration (Optional)

Any configuration options or environment variables.

### Example Usage (Optional)

Sample prompts or inputs users can try.
```

### requirements.txt Format

List dependencies with version constraints:

```
streamlit>=1.28.0
openai>=1.0.0
agno>=2.0.0
python-dotenv>=1.0.0
```

**Tips:**
- Include minimum version constraints (`>=`) for compatibility
- Don't over-constrain versions unless necessary
- Test with fresh installs to ensure all dependencies are listed

## Code Style Guidelines

### General Principles

- Write clean, readable code with meaningful variable names
- Add comments for complex logic
- Follow PEP 8 style guidelines for Python
- Handle errors gracefully with informative messages
- Keep functions focused and modular

### API Key Handling

```python
# ✅ Good: Use environment variables or user input
import os
import streamlit as st

api_key = os.getenv("OPENAI_API_KEY") or st.text_input("Enter API Key", type="password")

# ❌ Bad: Hardcoded keys
api_key = "sk-..."  # Never do this!
```

### Environment Variables

Create a `.env.example` file (not `.env`) showing required variables:

```bash
# .env.example
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### UI Framework

- **Streamlit** is the preferred UI framework for most apps
- Keep the UI simple and intuitive
- Provide clear labels and instructions
- Include loading indicators for long operations

### Code Organization

```python
# ✅ Good: Organized imports and structure
import os
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configuration
MODEL_NAME = "gpt-4"

# Functions
def process_query(query: str) -> str:
    """Process a user query and return a response."""
    # Implementation
    pass

# Main app
def main():
    st.title("My LLM App")
    # App logic

if __name__ == "__main__":
    main()
```

## Testing Guidelines

### Before Submitting

1. **Test with fresh environment**
   ```bash
   python -m venv test_env
   source test_env/bin/activate
   pip install -r requirements.txt
   python your_main_script.py
   ```

2. **Verify API key handling**
   - Test with missing API keys (should show helpful error)
   - Test with invalid API keys (should show helpful error)

3. **Test edge cases**
   - Empty inputs
   - Very long inputs
   - Special characters

4. **Check documentation accuracy**
   - Follow your own README instructions from scratch
   - Verify all links work
   - Ensure screenshots are current (if included)

### Validation Script

Use the provided validation script to check your environment:

```bash
python scripts/validate_env.py
# Or for specific providers:
python scripts/validate_env.py --provider openai --verbose
```

## Pull Request Process

### Before Submitting

1. **Test your app**: Ensure it runs without errors
2. **Check dependencies**: Verify all requirements are listed
3. **Review documentation**: Ensure README is complete and accurate
4. **Self-review**: Check your code for issues
5. **Update main README**: Add your app to the appropriate category list (if applicable)

### Creating Your Pull Request

1. Fork the repository
2. Create a new branch: `git checkout -b add-your-app-name`
3. Add your project files
4. Commit with a clear message: `git commit -m "Add [App Name]: brief description"`
5. Push to your fork: `git push origin add-your-app-name`
6. Open a Pull Request using our [PR template](.github/PULL_REQUEST_TEMPLATE.md)

### Pull Request Title Format

```
Add [App Name]: Brief description
```

Examples:
- `Add AI Recipe Generator: Create recipes from ingredients using GPT-4`
- `Add Local RAG Agent: Document Q&A with Ollama and ChromaDB`
- `Fix AI Travel Agent: Resolve API timeout issues`
- `Docs: Improve setup instructions for MCP agents`

### Pull Request Description

Include:
- What your app does
- Which LLM provider(s) it uses
- Any special requirements or setup steps
- Screenshots (if applicable)

## Review Criteria

Pull requests are reviewed based on:

| Criteria | Description |
|----------|-------------|
| **Functionality** | The app works as described |
| **Documentation** | README is clear and complete |
| **Code Quality** | Code is clean and well-organized |
| **Originality** | Demonstrates a unique or valuable use case |
| **Dependencies** | Requirements are properly specified |
| **Security** | No hardcoded secrets or vulnerabilities |

### Common Rejection Reasons

- ❌ App doesn't run or has errors
- ❌ Missing or incomplete documentation
- ❌ Duplicate of existing app without significant improvements
- ❌ Hardcoded API keys or secrets
- ❌ Missing requirements.txt
- ❌ Overly complex setup without justification

### Review Timeline

- Most PRs are reviewed within 3-5 business days
- Simple fixes may be merged faster
- Complex apps may require multiple review rounds

## Improving Existing Apps

When improving existing apps:

1. **Create an issue first** to discuss the proposed changes
2. **Keep changes focused** and minimal
3. **Maintain backward compatibility**
4. **Update documentation** if needed
5. **Test thoroughly** before submitting

### Types of Improvements Welcome

- Bug fixes with clear reproduction steps
- Performance improvements with benchmarks
- Additional LLM provider support
- Local model variants
- Better error handling
- Documentation clarifications

## Getting Help

### Quick Links

- 📝 **[New App Submission Template](.github/ISSUE_TEMPLATE/new_app_submission.md)** - Propose a new app
- 🐛 **[Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md)** - Report an issue
- 💡 **[Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md)** - Suggest improvements

### Community Support

- **Questions**: Open an issue with the "question" label
- **Bugs**: Open an issue with a detailed bug report
- **Discussions**: Use GitHub Discussions for general topics
- **Updates**: Follow [@Saboo_Shubham_](https://twitter.com/Saboo_Shubham_) on Twitter

### Helpful Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic API Reference](https://docs.anthropic.com/en/api)
- [LangChain Documentation](https://python.langchain.com/docs/)
- [Agno Documentation](https://docs.agno.com/)

## License

By contributing to this repository, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).

---

Thank you for contributing to Awesome LLM Apps! Your contributions help make LLM technology more accessible to everyone. 🙏

**Questions?** Open an issue or start a discussion - we're here to help!
