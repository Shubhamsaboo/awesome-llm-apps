# ⚡ Realtime Voice Agent

A basic realtime voice agent example using OpenAI's Realtime API. This demonstrates the core components for ultra-low latency voice conversations with minimal setup.

## 🎯 What This Demonstrates

- **Core Realtime Components**: RealtimeAgent, RealtimeRunner, and RealtimeSession
- **Basic Voice Conversation**: Ultra-low latency voice interaction
- **Function Tools**: Simple tools callable during voice conversation
- **Agent Handoffs**: Basic handoff to specialized agent
- **Event Handling**: Essential event processing for realtime sessions

## 🧠 Core Concept: Realtime Voice Processing

Realtime agents provide **ultra-low latency voice conversation** using OpenAI's Realtime API. Unlike traditional voice pipelines, realtime agents maintain persistent WebSocket connections for immediate audio processing. Think of realtime agents as **live conversation partners** that:

- Process audio and respond instantly with minimal latency
- Handle interruptions gracefully during conversation
- Maintain persistent connections for natural dialogue flow
- Support real-time tool execution and agent handoffs
- Apply safety guardrails during live generation

Based on the [official documentation](https://openai.github.io/openai-agents-python/realtime/quickstart/), realtime agents enable natural voice conversations with the lowest possible latency.

```
┌─────────────────────────────────────────────────────────────┐
│                   REALTIME VOICE WORKFLOW                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🎤 LIVE AUDIO INPUT                                        |
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    1. WEBSOCKET CONNECTION                 │
│  │ PERSISTENT  │    ◦ Continuous audio streaming            │
│  │ CONNECTION  │    ◦ Ultra-low latency pipeline            │
│  └─────────────┘    ◦ Real-time processing                  │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    2. INSTANT PROCESSING                   │
│  │ REALTIME    │    ◦ Immediate speech recognition          │
│  │ AGENTS      │    ◦ Live agent reasoning                  │
│  └─────────────┘    ◦ Real-time tool execution              │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    3. IMMEDIATE RESPONSE                   │
│  │   LIVE      │    ◦ Real-time audio generation            │
│  │ RESPONSE    │    ◦ Streaming audio output                │
│  └─────────────┘    ◦ Interruption handling                 │
│       │                                                     │
│       ▼                                                     │
│  🔊 INSTANT AUDIO OUTPUT                                    |
│                                                             │
│  ↺ CONTINUOUS CONVERSATION LOOP                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

1. **Install OpenAI Agents SDK**:
   ```bash
   pip install openai-agents
   ```

2. **Set up environment**:
   ```bash
   cp env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Run the basic realtime agent**:
   ```bash
   python agent.py
   ```

4. **Start talking**: The agent will respond in real-time. Try:
   - "What's the weather in Paris?"
   - "Book appointment tomorrow at 2pm"

## 🧪 What This Example Includes

### **Core Realtime Components**
Based on the [official guide](https://openai.github.io/openai-agents-python/realtime/guide/):
- **RealtimeAgent**: Agent with instructions, tools, and handoffs
- **RealtimeRunner**: Manages configuration and returns sessions  
- **RealtimeSession**: Single conversation session with event streaming

### **Basic Function Tools**
- `get_weather(city)`: Simple weather information
- `book_appointment(date, time, service)`: Basic appointment booking

### **Simple Agent Handoff**
- **Main Assistant**: General conversation agent
- **Billing Agent**: Specialized billing support (demonstrates handoff pattern)

### **Essential Event Handling**
- **Audio Transcripts**: User and assistant speech transcription
- **Tool Calls**: Function execution notifications
- **Error Events**: Basic error handling

## 🎯 Example Voice Interactions

### **Basic Conversation**
- "What's the weather in Paris?" → Tool call with instant response
- "Book appointment tomorrow at 2pm" → Appointment booking tool

### **Agent Handoff**
- "I need help with billing" → Handoff to billing support agent

## 🔧 Key Implementation Patterns

Based on the [official guide](https://openai.github.io/openai-agents-python/realtime/guide/):

### **1. Create RealtimeAgent**
```python
from agents.realtime import RealtimeAgent

agent = RealtimeAgent(
    name="Assistant",
    instructions="You are a helpful voice assistant...",
    tools=[get_weather, book_appointment],
    handoffs=[realtime_handoff(billing_agent)]
)
```

### **2. Set up RealtimeRunner**
```python
from agents.realtime import RealtimeRunner

runner = RealtimeRunner(
    starting_agent=agent,
    config={
        "model_settings": {
            "model_name": "gpt-4o-realtime-preview",
            "voice": "alloy",
            "modalities": ["text", "audio"]
        }
    }
)
```

### **3. Start Session and Handle Events**
```python
session = await runner.run()

async with session:
    async for event in session:
        if event.type == "response.audio_transcript.done":
            print(f"Assistant: {event.transcript}")
```

## 💡 Basic Realtime Concepts

From the [official guide](https://openai.github.io/openai-agents-python/realtime/guide/):

1. **Session Flow**: Create agents → Set up runner → Start session → Handle events
2. **Event Handling**: Listen for audio transcripts, tool calls, and errors
3. **Voice Configuration**: Choose from 6 voices (alloy, echo, fable, onyx, nova, shimmer)
4. **Turn Detection**: Server-side voice activity detection for natural conversation

## 📊 Realtime vs Traditional Voice Comparison

| Feature | Traditional Voice | Realtime Voice |
|---------|------------------|----------------|
| **Latency** | 2-5 seconds | <500ms |
| **Connection** | Request/Response | Persistent WebSocket |
| **Interruptions** | Limited | Natural handling |
| **Audio Processing** | Batched | Streaming |
| **Tool Execution** | Turn-based | Real-time |
| **Conversation Flow** | Structured | Natural |
| **API** | REST endpoints | WebSocket events |

## 🌟 Advanced Realtime Features

### **Voice Activity Detection (VAD)**
- **Server VAD**: OpenAI's optimized speech detection
- **Configurable Thresholds**: Adjust sensitivity for different environments
- **Silence Detection**: Intelligent turn boundary detection
- **Prefix Padding**: Capture speech start accurately

### **Audio Configuration Options**
- **Voice Selection**: Choose from 6 different voices (alloy, echo, fable, onyx, nova, shimmer)
- **Audio Formats**: Support for PCM16, G.711 μ-law, and G.711 A-law
- **Transcription Models**: Whisper integration for speech-to-text
- **Multi-Modal Support**: Text and audio modalities

### **Real-Time Guardrails**
Based on the [guide documentation](https://openai.github.io/openai-agents-python/realtime/guide/), realtime guardrails are:
- **Debounced**: Run periodically (not on every word) for performance
- **Configurable**: Adjustable debounce length (default 100 characters)
- **Non-Blocking**: Don't raise exceptions, generate events instead
- **Real-Time**: Can interrupt responses immediately when triggered

### **Session Event Types**
- **Audio Events**: `response.audio.delta`, `response.audio.done`
- **Transcription Events**: `response.audio_transcript.done`, `input_audio_transcription.completed`
- **Tool Events**: `response.function_call_arguments.done`
- **Lifecycle Events**: `session.created`, `session.updated`, `response.done`
- **Error Events**: `error`, `guardrail_tripped`

## 🚨 Requirements & Dependencies

### **Core Dependencies**
- `openai-agents>=1.0.0`: OpenAI Agents SDK with realtime support
- `python-dotenv>=1.0.0`: Environment variable management
- Python 3.9 or higher (required for realtime features)

### **API Requirements**
- **OpenAI API Key**: Required for Realtime API access
- **Model Access**: Access to `gpt-4o-realtime-preview` model
- **WebSocket Support**: Stable internet connection for persistent connections

### **System Requirements**
- **Real-Time Capable**: Low-latency network connection
- **Audio Hardware**: Microphone and speakers for voice interaction
- **Processing Power**: Sufficient CPU for real-time audio processing

## 🔧 Configuration Options

### **Model Settings**
```python
"model_settings": {
    "model_name": "gpt-4o-realtime-preview",  # Realtime model
    "voice": "alloy",                         # Voice selection
    "modalities": ["text", "audio"],          # Supported modalities
    "input_audio_format": "pcm16",           # Audio input format
    "output_audio_format": "pcm16"           # Audio output format
}
```

### **Turn Detection Settings**
```python
"turn_detection": {
    "type": "server_vad",           # Voice activity detection
    "threshold": 0.5,               # Detection sensitivity (0.0-1.0)
    "prefix_padding_ms": 300,       # Audio padding before speech
    "silence_duration_ms": 200      # Silence to detect turn end
}
```

### **Transcription Configuration**
```python
"input_audio_transcription": {
    "model": "whisper-1",           # Transcription model
    "language": "en",               # Language preference
    "prompt": "Custom prompt..."    # Domain-specific terms
}
```

## 🛡️ Safety and Guardrails

### **Real-Time Safety Features**
- **Debounced Processing**: Guardrails run periodically for performance
- **Immediate Intervention**: Can interrupt unsafe responses in real-time
- **Event-Based Alerts**: Generate `guardrail_tripped` events instead of exceptions
- **Configurable Sensitivity**: Adjust debounce length based on requirements

### **Safety Implementation**
```python
@output_guardrail
def sensitive_data_guardrail(ctx, agent, output: str) -> GuardrailFunctionOutput:
    if contains_sensitive_data(output):
        return GuardrailFunctionOutput(
            tripwire_triggered=True,
            output_info="Blocked sensitive data"
        )
    return GuardrailFunctionOutput(tripwire_triggered=False)
```

## 🎯 Production Considerations

### **Performance Optimization**
- **Connection Management**: Maintain persistent WebSocket connections
- **Error Recovery**: Implement automatic reconnection logic
- **Resource Monitoring**: Track memory and CPU usage during sessions
- **Event Processing**: Optimize event handling for high-throughput scenarios

### **Scalability Patterns**
- **Session Isolation**: Each user gets independent realtime sessions
- **Load Balancing**: Distribute sessions across multiple instances
- **Connection Pooling**: Manage WebSocket connections efficiently
- **Graceful Shutdown**: Handle session cleanup properly

### **Monitoring and Analytics**
- **Event Tracking**: Monitor all realtime events for insights
- **Performance Metrics**: Track latency, throughput, and error rates
- **User Analytics**: Analyze conversation patterns and success rates
- **Safety Metrics**: Monitor guardrail activation and effectiveness

## 🚨 Beta Considerations

As noted in the [official documentation](https://openai.github.io/openai-agents-python/realtime/quickstart/), realtime agents are currently in beta. Consider:

- **API Stability**: Expect potential breaking changes as the API evolves
- **Feature Development**: New capabilities may be added regularly
- **Testing Requirements**: Thorough testing recommended before production deployment
- **Feedback Channels**: Provide feedback to help improve the realtime experience

## 💡 Pro Tips

- **Start Simple**: Begin with basic realtime conversation before adding complex features
- **Monitor Events**: Use comprehensive event logging to understand behavior
- **Optimize Guardrails**: Balance safety with real-time performance requirements
- **Test Interruptions**: Ensure natural handling of conversation interruptions
- **Plan for Scale**: Design session management for production workloads

## 🔗 Related Documentation

- **[Realtime Quickstart](https://openai.github.io/openai-agents-python/realtime/quickstart/)**: Official getting started guide
- **[Realtime Guide](https://openai.github.io/openai-agents-python/realtime/guide/)**: Comprehensive realtime documentation
- **[Voice Agents](../README.md)**: Overview of all voice agent capabilities
- **[Agent Fundamentals](../../1_starter_agent/README.md)**: Basic agent concepts

## 🎯 Troubleshooting

### **Common Issues**
- **High Latency**: Check network connection and WebSocket stability
- **Audio Quality**: Verify microphone settings and audio formats
- **Event Processing**: Monitor event handling performance and errors
- **Guardrail Performance**: Optimize debounce settings for real-time requirements
- **Model Access**: Ensure access to `gpt-4o-realtime-preview` model

### **Debug Strategies**
- **Event Logging**: Enable comprehensive event debugging
- **Connection Monitoring**: Track WebSocket connection health
- **Performance Profiling**: Monitor CPU and memory usage during sessions
- **Audio Pipeline**: Verify audio input/output processing

## 🚀 Next Steps

After mastering realtime voice agents:
- **Production Deployment**: Scale realtime agents for production use
- **Custom Integrations**: Build realtime voice into existing applications
- **Advanced Features**: Explore cutting-edge realtime capabilities
- **Multi-Modal Experiences**: Combine realtime voice with other modalities
