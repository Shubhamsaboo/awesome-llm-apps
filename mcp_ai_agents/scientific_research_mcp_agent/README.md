# 🔬 Scientific Research MCP Agent

An AI-powered scientific research assistant that searches papers and retrieves structured experimental data using the [BGPT MCP](https://github.com/connerlambden/bgpt-mcp) server.

## Features

- Search scientific papers across all disciplines
- Get structured data from full-text studies (not just abstracts)
- Returns 25+ fields per paper: methods, results, sample sizes, quality scores, conclusions
- Evidence synthesis across multiple studies
- Free tier: 50 searches, no API key needed

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your OpenAI API key:
```bash
cp mcp_agent.secrets.yaml.example mcp_agent.secrets.yaml
# Edit mcp_agent.secrets.yaml with your OpenAI API key
```

3. Run the app:
```bash
streamlit run main.py
```

## How It Works

The agent connects to the BGPT remote MCP server (`https://bgpt.pro/mcp/sse`) which provides access to a curated database of scientific papers built from raw experimental data extracted from full-text studies. Unlike traditional literature databases that return titles and abstracts, BGPT returns structured data from the actual paper content.

## Example Queries

- "Find papers about CRISPR gene editing efficiency in human cells"
- "Compare sample sizes across CAR-T therapy clinical trials"
- "What methods are used to measure mRNA vaccine immunogenicity?"
- "Search for studies on checkpoint inhibitor response rates"
