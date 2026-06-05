#!/bin/bash
set -e

cd "$(dirname "$0")/../agent"

if [ ! -d ".venv" ]; then
  echo "Agent not set up. Run: npm run install:agent"
  exit 1
fi

source .venv/bin/activate

python -c "from src.seed import seed_if_needed; seed_if_needed()"

langgraph dev --port 8123
