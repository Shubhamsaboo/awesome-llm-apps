"""
DataSpoc Data Lake Agent

An AI agent that ingests data, queries it with SQL and natural language,
and manages cache freshness — all through DataSpoc's MCP servers and Python SDK.

Setup:
    pip install -r requirements.txt
    dataspoc-pipe init
    dataspoc-lens init

Usage:
    python dataspoc_data_lake_agent.py
"""

import os
from anthropic import Anthropic

# DataSpoc SDK imports
from dataspoc_lens import LensClient
from dataspoc_pipe import PipeClient

SYSTEM_PROMPT = """You are a data analyst agent with access to a data lake via DataSpoc.

You have two tools:
1. PipeClient — manage data ingestion (list pipelines, run them, check status, read logs)
2. LensClient — query the data lake (list tables, get schemas, run SQL, ask in natural language, manage cache)

When the user asks a question:
1. First check if the data is cached and fresh. If stale, refresh it.
2. Try to answer using SQL queries or natural language ask().
3. Show the SQL you used and explain the results.
4. If data is missing, suggest which pipeline to run.

Always be honest about what data is available and what isn't."""


def run_agent():
    client = Anthropic()

    # Initialize DataSpoc clients
    pipe = PipeClient()
    lens = LensClient()

    # Show available data
    tables = lens.tables()
    pipelines = pipe.pipelines()

    print("=" * 60)
    print("  DataSpoc Data Lake Agent")
    print("=" * 60)
    print(f"\n  Tables available: {len(tables)}")
    for t in tables:
        print(f"    - {t}")
    print(f"\n  Pipelines configured: {len(pipelines)}")
    for p in pipelines:
        print(f"    - {p}")
    print(f"\n  Type your question or 'quit' to exit.\n")

    messages = []

    # Build context about available data
    schema_context = ""
    for t in tables[:10]:  # Limit to 10 tables for context
        cols = lens.schema(t)
        col_names = ", ".join([c["column_name"] for c in cols])
        schema_context += f"Table '{t}': {col_names}\n"

    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit"):
            break

        messages.append({"role": "user", "content": user_input})

        # Try to answer with DataSpoc
        try:
            # Check cache freshness first
            cache_status = lens.cache_status()
            stale_tables = [s["table"] for s in cache_status if s["status"] == "stale"]
            if stale_tables:
                print(f"\n  [Refreshing {len(stale_tables)} stale table(s)...]")
                lens.cache_refresh_stale()

            # Use AI ask for natural language questions
            result = lens.ask(user_input)

            if result.get("error"):
                # Fall back to Claude for interpretation
                context = f"Available tables and schemas:\n{schema_context}\nUser question: {user_input}\nDataSpoc returned error: {result['error']}"
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": context}],
                )
                answer = response.content[0].text
            else:
                sql = result.get("sql", "")
                rows = result.get("rows", [])
                columns = result.get("columns", [])
                duration = result.get("duration", 0)

                # Format results
                answer = f"SQL: {sql}\n\n"
                if columns and rows:
                    answer += " | ".join(columns) + "\n"
                    answer += "-" * 40 + "\n"
                    for row in rows[:20]:  # Limit display
                        answer += " | ".join(str(v) for v in row) + "\n"
                    answer += f"\n({len(rows)} rows, {duration:.3f}s)"
                else:
                    answer += "No results returned."

        except Exception as e:
            answer = f"Error: {e}"

        print(f"\nAgent: {answer}\n")
        messages.append({"role": "assistant", "content": answer})

    lens.close()
    print("\nGoodbye!")


if __name__ == "__main__":
    run_agent()
