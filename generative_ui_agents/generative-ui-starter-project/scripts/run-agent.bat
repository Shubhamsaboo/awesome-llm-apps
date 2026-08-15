@echo off
cd /d "%~dp0..\agent"
npx @langchain/langgraph-cli dev --port 8123 --no-browser
