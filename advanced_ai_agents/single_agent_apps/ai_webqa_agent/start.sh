#!/bin/bash

# WebQA Agent Docker Startup Script

set -e

REPO_BASE_URL="https://raw.githubusercontent.com/MigoXLab/webqa-agent"
BRANCH="${WEBQA_BRANCH:-main}"

echo "🚀 Starting WebQA Agent Docker container..."

# Create necessary directories
mkdir -p config logs reports

# Check if configuration file exists
if [ ! -f "config.yaml" ] && [ ! -f "config/config.yaml" ]; then
    echo "❌ Configuration file not found"
    echo "Please steup the configuration file template first:"
    exit 1
fi

# Download docker-compose.yml (if it doesn't exist)
if [ ! -f "docker-compose.yml" ]; then
    echo "📥 Downloading docker-compose.yml..."
    curl -fsSL "$REPO_BASE_URL/$BRANCH/docker-compose.yml" -o docker-compose.yml || {
        echo "❌ Failed to download docker-compose.yml"
        exit 1
    }
fi

# Determine configuration file path
if [ -f "config.yaml" ]; then
    CONFIG_FILE="config.yaml"
    echo "✅ Found configuration file: config.yaml"
elif [ -f "config/config.yaml" ]; then
    CONFIG_FILE="config/config.yaml"
    echo "✅ Found configuration file: config/config.yaml"
else
    echo "❌ Error: Configuration file not found"
    exit 1
fi

# Simplified configuration validation
echo "🔍 Validating configuration file..."

# Check YAML syntax (prefer yq, fallback to Python+PyYAML)
YAML_STATUS=0
if command -v yq >/dev/null 2>&1; then
    if ! yq eval '.' "$CONFIG_FILE" >/dev/null 2>&1; then
        echo "❌ Configuration file YAML syntax error (yq check)"
        YAML_STATUS=1
    fi
elif python3 -c "import yaml" >/dev/null 2>&1; then
    if ! python3 -c "import yaml; yaml.safe_load(open('$CONFIG_FILE'))" >/dev/null 2>&1; then
        echo "❌ Configuration file YAML syntax error (PyYAML check)"
        YAML_STATUS=1
    fi
else
    echo "⚠️  Skipping YAML syntax check (yq or PyYAML not installed)"
fi

if [ $YAML_STATUS -ne 0 ]; then
    exit 1
fi

# Basic field checks
if ! grep -q "url:" "$CONFIG_FILE"; then
    echo "❌ target.url configuration not found"
    exit 1
fi

if ! grep -q "llm_config:" "$CONFIG_FILE"; then
    echo "❌ llm_config configuration not found"
    exit 1
fi

if ! grep -q "test_config:" "$CONFIG_FILE"; then
    echo "❌ test_config configuration not found"
    exit 1
fi

# Check if any tests are enabled (support True/true)
if ! grep -i "enabled: *true" "$CONFIG_FILE"; then
    echo "❌ All tests are disabled, please enable at least one test item"
    exit 1
fi

# Check for API Key in environment variables or configuration file
if [ -z "$OPENAI_API_KEY" ] && ! grep -q "api_key:" "$CONFIG_FILE"; then
    echo "❌ LLM API Key not configured (requires OPENAI_API_KEY environment variable or llm_config.api_key in configuration file)"
    exit 1
fi

echo "✅ Basic configuration check passed"

# Create necessary directories
mkdir -p logs reports

# Start container
echo "🚀 Starting container..."
docker-compose up

echo "✅ Container startup completed!"
echo "📋 View logs: docker-compose logs -f"
echo "🛑 Stop service: docker-compose down"
