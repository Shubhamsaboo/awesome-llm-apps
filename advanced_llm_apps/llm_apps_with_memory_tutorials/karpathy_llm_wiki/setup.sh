#!/usr/bin/env bash
# Bootstrap script for Karpathy LLM Wiki.
#
# This is a thin wrapper. The full setup lives in the standalone repo:
#   https://github.com/MehmetGoekce/llm-wiki
#
# Run this to clone the standalone implementation and launch its interactive
# setup (which configures Logseq vs. Obsidian, wiki path, schema, and the
# /wiki Claude Code skill).

set -euo pipefail

REPO_URL="https://github.com/MehmetGoekce/llm-wiki.git"
TARGET_DIR="${LLM_WIKI_DIR:-$HOME/llm-wiki}"

if [ -d "$TARGET_DIR" ]; then
  echo "llm-wiki already exists at $TARGET_DIR — pulling latest."
  git -C "$TARGET_DIR" pull --ff-only
else
  echo "Cloning llm-wiki to $TARGET_DIR..."
  git clone --depth 1 "$REPO_URL" "$TARGET_DIR"
fi

cd "$TARGET_DIR"
echo
echo "Running interactive setup..."
exec ./setup.sh
