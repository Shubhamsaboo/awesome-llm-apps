# DataSpoc Data Lake Agent

An AI agent that manages data ingestion and queries a cloud data lake using [DataSpoc](https://github.com/dataspoclab) — an open-source data platform with native MCP and SDK support.

## What it does

- Discovers available tables and their schemas
- Checks cache freshness and refreshes stale data automatically
- Answers questions in natural language (generates SQL, executes, explains)
- Lists and runs data ingestion pipelines
- Works with S3, GCS, Azure, or local Parquet files

## Stack

- **DataSpoc Pipe** — data ingestion (400+ Singer sources to Parquet)
- **DataSpoc Lens** — SQL queries via DuckDB + AI natural language queries
- **Anthropic Claude** — for interpreting results and handling edge cases

## Setup

```bash
pip install -r requirements.txt

# Initialize DataSpoc
dataspoc-pipe init
dataspoc-lens init

# Add a data source (example: local CSV)
dataspoc-pipe add my-source

# Register the bucket with Lens
dataspoc-lens add-bucket file:///path/to/lake

# Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-...

# Run the agent
python dataspoc_data_lake_agent.py
```

## MCP Alternative

Instead of the Python SDK, you can use DataSpoc as MCP servers with Claude Desktop:

```json
{
  "mcpServers": {
    "dataspoc-lens": {
      "command": "dataspoc-lens",
      "args": ["mcp"]
    },
    "dataspoc-pipe": {
      "command": "dataspoc-pipe",
      "args": ["mcp"]
    }
  }
}
```

## Links

- [DataSpoc Website](https://dataspoc.com)
- [Pipe GitHub](https://github.com/dataspoclab/dataspoc-pipe)
- [Lens GitHub](https://github.com/dataspoclab/dataspoc-lens)
