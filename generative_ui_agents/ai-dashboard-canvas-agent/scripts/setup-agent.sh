#!/bin/bash

# Navigate to the agent directory
cd "$(dirname "$0")/../agent" || exit 1

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
  python3 -m venv .venv || python -m venv .venv
fi

# Activate the virtual environment
source .venv/bin/activate

# Install requirements using pip3 or pip
(pip3 install -r requirements.txt || pip install -r requirements.txt)
