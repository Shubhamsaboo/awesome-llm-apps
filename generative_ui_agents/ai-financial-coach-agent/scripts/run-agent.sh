#!/bin/bash

# Navigate to the agent directory
cd "$(dirname "$0")/../agent" || exit 1

# Activate the virtual environment
source .venv/bin/activate

# Run the agent
uv run main.py
