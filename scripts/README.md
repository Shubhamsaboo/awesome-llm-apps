# Scripts

Utility scripts for the Awesome LLM Apps repository.

## validate_env.py

A quick setup verification tool that checks if required dependencies are installed and API keys are properly configured for each LLM provider.

### Usage

```bash
# Run full environment validation
python scripts/validate_env.py

# Check a specific provider
python scripts/validate_env.py --provider openai

# Only check if core packages are installed
python scripts/validate_env.py --check-packages

# Show detailed output with masked API key values
python scripts/validate_env.py --verbose
```

### Supported Providers

- **OpenAI** - GPT-4, GPT-3.5-turbo
- **Anthropic** - Claude models
- **Google** - Gemini models
- **Groq** - Fast inference
- **Cohere** - Embeddings and chat
- **OpenRouter** - Multi-model routing
- **Together AI** - Distributed inference
- **Perplexity** - Research models
- **Mistral AI** - Mistral models

### Supporting Services

The script also checks for optional supporting services:

- Tavily (Web Search)
- Serper (Google Search)
- Exa (Semantic Search)
- Firecrawl (Web Scraping)
- ElevenLabs (Text-to-Speech)
- Qdrant (Vector Database)

### Requirements

The script has no external dependencies and works with Python 3.8+. It will optionally use `python-dotenv` to load `.env` files if available.
