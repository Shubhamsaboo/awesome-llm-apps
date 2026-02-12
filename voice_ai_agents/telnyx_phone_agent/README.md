# 📞 Telnyx Phone AI Agent

A voice-powered AI phone agent built with Telnyx Call Control and OpenAI GPT-4o-mini. The agent answers incoming phone calls, listens to the caller using speech recognition, generates intelligent responses with an LLM, and speaks the reply back in real time.

## Features

- **Incoming Call Handling**: Automatically answers calls to your Telnyx number
- **Speech Recognition**: Captures caller speech using Telnyx's built-in gather functionality
- **LLM-Powered Responses**: Processes speech input through OpenAI GPT-4o-mini for intelligent replies
- **Text-to-Speech**: Speaks AI responses back to the caller with natural-sounding voice
- **Conversation Memory**: Maintains per-call conversation history for multi-turn dialogue
- **Webhook-Based**: Event-driven architecture using Telnyx Call Control webhooks

## How to Run

1. **Setup Environment**
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/voice_ai_agents/telnyx_phone_agent

   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   ```bash
   cp .env.example .env
   ```
   Fill in your credentials:
   - **TELNYX_API_KEY**: Get from [Telnyx Mission Control Portal](https://portal.telnyx.com)
   - **TELNYX_CONNECTION_ID**: Create a Call Control Application in Telnyx and copy the ID
   - **OPENAI_API_KEY**: Get from [OpenAI Platform](https://platform.openai.com)

3. **Setup Telnyx**
   - Create a [Telnyx account](https://telnyx.com/sign-up)
   - Buy a phone number in Mission Control
   - Create a Call Control Application
   - Assign the phone number to the application
   - Set the webhook URL to your server (see step 5)

4. **Run the Server**
   ```bash
   uvicorn telnyx_phone_agent:app --port 8000
   ```

5. **Expose with ngrok** (for local development)
   ```bash
   ngrok http 8000
   ```
   Copy the ngrok HTTPS URL and set it as the webhook URL in your Telnyx Call Control Application:
   `https://your-ngrok-url.ngrok.io/webhooks/call`

6. **Call your Telnyx number** and start talking to your AI agent!

## Architecture

```
Caller --> Telnyx Number --> Call Control Webhook --> FastAPI Server
                                                        |
                                                        v
                                                   OpenAI GPT-4o-mini
                                                        |
                                                        v
                                              Telnyx TTS (speak back)
```

## Call Flow

1. Caller dials your Telnyx number
2. Telnyx sends a `call.initiated` webhook; the server answers the call
3. Server greets the caller using text-to-speech
4. Server listens for caller speech via `gather_using_speak`
5. Caller's speech is sent to OpenAI for processing
6. AI response is spoken back to the caller
7. Steps 4-6 repeat until the caller hangs up
