# 📄 AI Layout-Preserving PDF Translator Agent with Streamlit

An intelligent document translation assistant that translates complex technical papers, contracts, and research documents into any language while **strictly preserving 1:1 original layout structure, tables, typography hierarchy, and formulas**.

> 🌟 **Powered by [pdf-translate](https://github.com/lxsssssss/pdf-translate)**: Looking for an automated command-line engine or drop-in Agent Skill for Claude Code, Antigravity, and Cursor? Check out the full open-source framework: [lxsssssss/pdf-translate](https://github.com/lxsssssss/pdf-translate).

---

## Features

- **Strict 1:1 Layout Preservation**: Keeps document headers, bullet lists, bold emphasis, and structural divisions intact without layout collapse.
- **Table Structure Retention**: Retains table column count, header alignments, and inline markdown format exactly.
- **Two-Stage Schema Protocol**: Decouples document schema extraction from semantic translation to eliminate hallucinations in long-context clauses.
- **Interactive Dual-Column Comparison**: Side-by-side synchronized visual comparison between original and reconstructed translated document.
- **Universal LLM Compatibility**: Works out-of-the-box with OpenAI (`gpt-4o`, `gpt-4o-mini`), DeepSeek, OpenRouter, or any OpenAI-compatible API endpoint.
- **One-Click Export**: Export the translated document directly as structured Markdown.

---

## How It Works

```
┌─────────────────┐       ┌────────────────────────┐       ┌──────────────────────┐
│  Source PDF /   │  ───► │   Two-Stage Pipeline   │  ───► │  1:1 Dual-Column     │
│  Sample Doc     │       │ (Schema + Translation) │       │ Synchronized Viewer  │
└─────────────────┘       └────────────────────────┘       └──────────────────────┘
```

1. **Extraction**: `pypdf` extracts pages, preserving paragraph blocks and tabular text elements.
2. **Schema Contract**: The agent guarantees that all structural elements (headings, tables, lists) follow a rigid format contract.
3. **LLM Translation**: Translates text nodes into the target language while locking code blocks, model names, and table cell alignments.
4. **Side-by-Side Audit**: Renders the original and translated versions side-by-side for human visual inspection.

---

## Requirements

- Python 3.9+
- OpenAI API Key (or DeepSeek / OpenRouter key)
- Required packages (see `requirements.txt`)

---

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/single_agent_apps/ai_pdf_translator_agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

1. Start the Streamlit application:
   ```bash
   streamlit run pdf_translator_agent.py
   ```

2. Open your browser at `http://localhost:8501`.

3. Configure your API provider and API key in the sidebar.

4. Upload your PDF or toggle **Use Sample Document** (featuring *Attention Is All You Need*), then click **🚀 Start Layout-Preserving Translation**!
