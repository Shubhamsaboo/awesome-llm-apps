"""
AI Agent with Persistent Memory via Contexto

Contexto is a self-hosted context engine that runs as an OpenAI-compatible
proxy on port 4010. Point the openai client at localhost:4010 instead of
the upstream provider — memory injection happens automatically on every
request with no SDK changes required.

Run this script twice to see cross-session memory in action:
  - First run:  the agent learns your name and preferences.
  - Second run: the agent recalls what was said in the previous session.
"""

import os
from openai import OpenAI

# Point the client at the Contexto proxy instead of the upstream API.
# Contexto intercepts each request, retrieves relevant memories, injects
# them into the system prompt, and forwards the request to OpenRouter.
client = OpenAI(
    base_url="http://localhost:4010/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "placeholder"),
)

# A stable user ID lets Contexto scope memories to this agent session.
USER_ID = "demo-user"

# Conversation history kept in-memory for the current session only.
# Contexto handles persistence across sessions automatically.
messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful assistant. Be concise. "
            "If you recall information about the user from a previous session, "
            "reference it naturally."
        ),
    }
]

print("AI Agent with Contexto Memory")
print("Type 'quit' to exit.\n")

# Seed the first turn with a fixed opener so the demo is self-contained.
turns = [
    "Hi! My name is Alex and I'm building an AI agent for trip planning.",
    "I prefer budget travel and I love hiking.",
    "What kind of trips would you suggest for me?",
]

for user_input in turns:
    print(f"You: {user_input}")
    messages.append({"role": "user", "content": user_input})

    # Contexto intercepts this call:
    #   1. Retrieves memories stored under USER_ID from previous sessions.
    #   2. Injects them into the request before forwarding to the LLM.
    #   3. Stores the new exchange as a memory after the response returns.
    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=messages,
        extra_headers={"X-Contexto-User-Id": USER_ID},
    )

    assistant_reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": assistant_reply})
    print(f"Agent: {assistant_reply}\n")

print("Session complete. Run the script again to see Contexto recall this session.")
