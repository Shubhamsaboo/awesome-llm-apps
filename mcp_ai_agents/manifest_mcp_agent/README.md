# 🗺️ Manifest MCP Agent

A Streamlit app that turns any URL into a structured action map using the [Manifest API](https://omfang.io/manifest-overview), then uses an LLM to reason about what an agent could do on that page.

## What it does

- Paste any URL and call the Manifest API with one click
- See every action on the page: buttons, forms, inputs — with types, required flags, and cross-action dependencies
- Ask an LLM (OpenAI or Anthropic) to describe how an agent would interact with the page based on the manifest
- No screenshots, no brittle selectors — structured JSON that agents can act on directly

## Why Manifest?

Most agents interact with web UIs by screenshotting and guessing, or through hand-written selectors that break on every redesign. Manifest sits between a browser tool and your agent logic: it returns a structured description of what the agent can *do* on the page, not just what's on it.

## Setup

### Requirements

- Python 3.9+
- A Manifest API key — get one free at [app.manifest.omfang.io](https://app.manifest.omfang.io)
- An OpenAI or Anthropic API key

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd mcp_ai_agents/manifest_mcp_agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your API keys:
   ```bash
   cp .env.example .env
   # Edit .env and add your keys
   ```

4. Run the app:
   ```bash
   streamlit run main.py
   ```

## Usage

1. Enter any URL in the input field
2. Click **Generate Manifest** to fetch the action map
3. Browse the structured JSON — every action with its locator, type, required flag, and dependencies
4. Click **Explain agent plan** to have the LLM describe how an agent would interact with the page

## Example output

```json
{
  "url": "https://example.com/checkout",
  "current_page_state": "Checkout form with email and payment fields",
  "actions": [
    {
      "id": "email",
      "label": "Email address",
      "type": "email",
      "required": true,
      "locator": {"css": "input[type='email']", "role": "input"}
    },
    {
      "id": "place-order",
      "label": "Place order",
      "type": "button",
      "required": false,
      "requires": ["email", "card-number"]
    }
  ]
}
```

## Links

- [Manifest homepage](https://omfang.io/manifest-overview)
- [Manifest docs](https://omfang.io/manifest-docs)
- [Live demo (no account needed)](https://demo.manifest.omfang.io/demo)
- [PyPI](https://pypi.org/project/manifest-api/)
