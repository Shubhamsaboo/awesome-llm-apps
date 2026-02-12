"""
Telnyx Phone AI Agent

An AI-powered phone agent that answers calls, listens to the caller,
generates responses using OpenAI's GPT-4o-mini, and speaks the response
back over the phone using Telnyx Call Control.

Requirements:
    - Telnyx account with a Call Control Application and phone number
    - OpenAI API key
    - A public URL for webhooks (use ngrok for local development)

Usage:
    1. Copy .env.example to .env and fill in your credentials
    2. pip install -r requirements.txt
    3. uvicorn telnyx_phone_agent:app --port 8000
    4. Expose port 8000 with ngrok: ngrok http 8000
    5. Set the ngrok URL as your Telnyx Call Control webhook
    6. Call your Telnyx number
"""

import os
import json
from fastapi import FastAPI, Request
from openai import OpenAI
import telnyx
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configuration
telnyx.api_key = os.getenv("TELNYX_API_KEY")
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TELNYX_CONNECTION_ID = os.getenv("TELNYX_CONNECTION_ID")

# Store conversation history per call
conversation_history = {}


@app.post("/webhooks/call")
async def handle_call_webhook(request: Request):
    """Handle Telnyx Call Control webhooks."""
    body = await request.json()
    event_type = body.get("data", {}).get("event_type", "")
    payload = body.get("data", {}).get("payload", {})
    call_control_id = payload.get("call_control_id", "")

    if event_type == "call.initiated":
        # Answer the incoming call
        call = telnyx.Call.create(call_control_id=call_control_id)
        call.answer()

    elif event_type == "call.answered":
        # Greet the caller
        call = telnyx.Call.create(call_control_id=call_control_id)
        call.speak(
            payload="Hello! I am your AI phone assistant. How can I help you today?",
            voice="female",
            language="en-US",
        )

    elif event_type == "call.speak.ended":
        # After speaking, listen for user input
        call = telnyx.Call.create(call_control_id=call_control_id)
        call.gather_using_speak(
            payload="I'm listening.",
            voice="female",
            language="en-US",
            minimum_digits=1,
            maximum_digits=100,
            timeout_millis=10000,
            inter_digit_timeout_millis=3000,
        )

    elif event_type == "call.gather.ended":
        # Process user speech with the LLM
        speech_result = payload.get("speech", {}).get("result", "")
        digit_result = payload.get("digits", "")
        user_text = speech_result or digit_result

        if not user_text:
            return {"status": "no input"}

        # Build conversation context
        if call_control_id not in conversation_history:
            conversation_history[call_control_id] = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful phone assistant. Keep responses concise "
                        "and conversational, under 2 sentences. Be friendly and direct."
                    ),
                }
            ]

        conversation_history[call_control_id].append(
            {"role": "user", "content": user_text}
        )

        # Generate response with OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history[call_control_id],
        )

        ai_response = response.choices[0].message.content
        conversation_history[call_control_id].append(
            {"role": "assistant", "content": ai_response}
        )

        # Speak the AI response back to the caller
        call = telnyx.Call.create(call_control_id=call_control_id)
        call.speak(
            payload=ai_response,
            voice="female",
            language="en-US",
        )

    elif event_type == "call.hangup":
        # Clean up conversation history
        conversation_history.pop(call_control_id, None)

    return {"status": "ok"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
