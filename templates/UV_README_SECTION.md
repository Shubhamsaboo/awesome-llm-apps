## Installation

This project uses [UV](https://github.com/astral-sh/uv) for fast, reliable Python package management. UV provides 10-100x faster installation times compared to traditional pip.

### Using UV (Recommended)

1. **Install UV** (if not already installed):
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Clone and setup the project**:
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

4. **Run the application**:
   ```bash
   # For scripts
   uv run python main.py
   
   # For Streamlit apps
   uv run streamlit run app.py
   
   # For FastAPI apps
   uv run uvicorn app:app --reload
   ```

### Using pip (Traditional)

If you prefer using pip:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Development Setup

For development with additional tools:

```bash
# Install with dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run formatting
uv run black .
```

### Adding New Dependencies

```bash
# Add a new package
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Update all dependencies
uv sync --upgrade
```

### Troubleshooting

1. **UV command not found**: Make sure UV is in your PATH:
   ```bash
   export PATH="$HOME/.cargo/bin:$PATH"
   ```

2. **Python version issues**: This project requires Python 3.12+:
   ```bash
   python --version  # Should show 3.12 or higher
   ```

3. **Dependency conflicts**: Let UV resolve them:
   ```bash
   uv sync --refresh
   ```

For more information about UV, visit the [official documentation](https://github.com/astral-sh/uv).