"""
GhostClaw — Bare-Metal Telegram AI Agent

A minimal example of wiring a Telegram bot to Anthropic's Claude API
with persistent conversation history and tool use.

Usage:
    export ANTHROPIC_API_KEY="your-key"
    export TELEGRAM_BOT_TOKEN="your-token"
    python ghostclaw_telegram_agent.py
"""

import os
import json
import sqlite3
import logging
from datetime import datetime

import anthropic
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ghostclaw")

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
MODEL = "claude-sonnet-4-20250514"
MAX_HISTORY = 20  # messages per chat to keep in context

# --- Database ---

DB_PATH = "ghostclaw.db"


def init_db():
    """Create the messages table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_message(chat_id: int, role: str, content: str):
    """Save a message to the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO messages (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (chat_id, role, content, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_history(chat_id: int) -> list[dict]:
    """Get recent conversation history for a chat."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
        (chat_id, MAX_HISTORY),
    ).fetchall()
    conn.close()
    # Reverse so oldest first
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


# --- Claude ---

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are GhostClaw, a helpful AI assistant on Telegram.
You're direct, friendly, and concise. You help with research, writing,
analysis, and general questions. Keep responses short unless asked for detail."""

# Example tools — extend these for your use case
TOOLS = [
    {
        "name": "get_current_time",
        "description": "Get the current date and time.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def handle_tool_call(tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return the result."""
    if tool_name == "get_current_time":
        return json.dumps({"time": datetime.now().isoformat()})
    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def ask_claude(chat_id: int, user_message: str) -> str:
    """Send a message to Claude with conversation history and return the response."""
    save_message(chat_id, "user", user_message)
    history = get_history(chat_id)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        messages=history,
    )

    # Handle tool use loop
    while response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = handle_tool_call(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        # Add assistant response and tool results to history
        history.append({"role": "assistant", "content": response.content})
        history.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=history,
        )

    # Extract text response
    reply = ""
    for block in response.content:
        if hasattr(block, "text"):
            reply += block.text

    save_message(chat_id, "assistant", reply)
    return reply


# --- Telegram ---


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(
        "Hey. I'm GhostClaw. Ask me anything — research, writing, analysis, whatever you need."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages."""
    chat_id = update.effective_chat.id
    user_message = update.message.text

    logger.info(f"Message from {chat_id}: {user_message[:50]}...")

    try:
        reply = ask_claude(chat_id, user_message)
        # Telegram has a 4096 char limit per message
        for i in range(0, len(reply), 4096):
            await update.message.reply_text(reply[i : i + 4096])
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Something went wrong. Try again.")


def main():
    """Start the bot."""
    init_db()
    logger.info("GhostClaw starting...")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Listening on Telegram...")
    app.run_polling()


if __name__ == "__main__":
    main()
