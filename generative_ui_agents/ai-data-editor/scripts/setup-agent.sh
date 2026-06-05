#!/bin/bash
set -e

cd "$(dirname "$0")/../agent"

if ! command -v uv &> /dev/null; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

if [ ! -d ".venv" ]; then
  echo "Creating Python virtual environment..."
  uv venv
fi

echo "Installing Python dependencies..."
uv pip install -e .

echo "Agent setup complete."
