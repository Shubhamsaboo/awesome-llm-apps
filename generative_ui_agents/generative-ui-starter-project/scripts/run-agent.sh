#!/bin/bash
cd "$(dirname "$0")/../agent" || exit 1
npx @langchain/langgraph-cli dev --port 8123 --no-browser
