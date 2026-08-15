#!/bin/bash
set -e

echo "========================================="
echo "[entrypoint] Starting: Google ADK starter"
echo "[entrypoint] Time: $(date -u)"
echo "[entrypoint] PORT=${PORT:-not set}"
echo "========================================="

# Check critical env vars
if [ -z "$GOOGLE_API_KEY" ]; then
  echo "[entrypoint] WARNING: GOOGLE_API_KEY is not set! Agent will fail."
else
  echo "[entrypoint] GOOGLE_API_KEY: set (${#GOOGLE_API_KEY} chars)"
fi

# Start Python agent on port 8000 (override PORT which Railway sets to 3000)
echo "[entrypoint] Starting ADK agent on port 8000..."
cd /app/agent
PORT=8000 python main.py 2>&1 | sed 's/^/[agent] /' &
AGENT_PID=$!
cd /app

sleep 2

if kill -0 $AGENT_PID 2>/dev/null; then
  echo "[entrypoint] ADK agent started (PID: $AGENT_PID)"
else
  echo "[entrypoint] ERROR: ADK agent failed to start!"
fi

# Start Next.js frontend
echo "[entrypoint] Starting Next.js on port ${PORT:-3000}..."
PORT=${PORT:-3000} npx next start --port ${PORT:-3000} 2>&1 | sed 's/^/[nextjs] /' &
NEXTJS_PID=$!

echo "[entrypoint] Both processes running. Waiting..."

wait -n $AGENT_PID $NEXTJS_PID
EXIT_CODE=$?
echo "[entrypoint] A process exited with code $EXIT_CODE"
kill $AGENT_PID $NEXTJS_PID 2>/dev/null || true
exit $EXIT_CODE
