#!/bin/bash
set -e

echo "[entrypoint] Starting: langgraph-python starter"

if [ -z "$OPENAI_API_KEY" ]; then
  echo "[entrypoint] WARNING: OPENAI_API_KEY not set!"
else
  echo "[entrypoint] OPENAI_API_KEY: set"
fi

# Start agent via AG-UI protocol (serve.py wraps the original graph)
echo "[entrypoint] Starting agent on port 8123..."
AGENT_PORT=8123 python serve.py 2>&1 &
AGENT_PID=$!

sleep 3

# Start Next.js standalone
echo "[entrypoint] Starting Next.js on port ${PORT:-3000}..."
HOSTNAME=0.0.0.0 PORT=${PORT:-3000} node server.js 2>&1 &
NEXT_PID=$!

echo "[entrypoint] Agent=$AGENT_PID Next=$NEXT_PID"
wait -n $AGENT_PID $NEXT_PID
exit $?
