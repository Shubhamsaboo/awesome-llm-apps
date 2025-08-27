# 🎙️ Tutorial 11: Voice Agents

Master voice-enabled AI agents with the OpenAI Agents SDK! This tutorial demonstrates how to build conversational voice agents using speech-to-text, text-to-speech, and intelligent agent workflows for natural voice interactions.

## 🎯 What You'll Learn

- **Voice Pipeline Architecture**: Complete speech ↔ text ↔ speech workflow
- **Static Voice Processing**: Turn-based voice interaction with recorded audio
- **Streaming Voice Processing**: Real-time voice conversation with live audio
- **Multi-Language Support**: Automatic language detection and agent handoffs
- **Voice-Optimized Tools**: Design tools specifically for voice interactions
- **Audio Management**: Recording, playback, and streaming audio utilities

## 🧠 Core Concept: Voice Agents

Voice agents combine the power of AI language models with speech processing to create natural conversational interfaces. Think of voice agents as **AI assistants you can talk to naturally** that:

- Listen to your speech and convert it to text
- Process your request with intelligent AI agents
- Use tools and make decisions like text-based agents
- Convert responses back to natural speech
- Handle multi-turn conversations seamlessly

```
┌─────────────────────────────────────────────────────────────┐
│                     VOICE AGENT SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🎤 USER SPEECH                                             │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    1. SPEECH-TO-TEXT                       │
│  │   AUDIO     │    ◦ Convert speech to text                │
│  │  PIPELINE   │    ◦ Handle multiple languages             │
│  └─────────────┘                                            │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    2. AGENT PROCESSING                     │
│  │    AGENT    │    ◦ Multi-agent workflows                 │
│  │ ECOSYSTEM   │    ◦ Tool calling & handoffs               │
│  └─────────────┘    ◦ Context management                    │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    3. TEXT-TO-SPEECH                       │
│  │   SPEECH    │    ◦ Convert response to speech            │
│  │ SYNTHESIS   │    ◦ Natural voice output                  │
│  └─────────────┘                                            │
│       │                                                     │
│       ▼                                                     │
│  🔊 AI RESPONSE                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Tutorial Overview

This tutorial demonstrates **three core voice interaction patterns**:

### **1. Static Voice Processing** (`static/`)
- **Turn-based interaction**: Record → Process → Respond
- **Complete audio processing**: Full utterance before processing  
- **Simpler implementation**: Easier to understand and debug
- **Best for**: Voice commands, structured interactions

### **2. Streaming Voice Processing** (`streamed/`)
- **Real-time interaction**: Continuous listening and responding
- **Live audio streaming**: Process audio as it arrives
- **Activity detection**: Automatic speech start/stop detection
- **Best for**: Natural conversations, voice assistants

### **3. Realtime Voice Processing** (`realtime/`)
- **Ultra-low latency**: WebSocket-based persistent connections
- **Interruption handling**: Natural conversation interruptions
- **Realtime API**: OpenAI's newest voice technology
- **Best for**: Live conversations, minimal latency requirements

## 📁 Project Structure

```
11_voice/
├── README.md                          # This file - voice agents overview
├── static/                            # Static voice processing example
│   ├── agent.py                      # Complete static voice agent
│   ├── util.py                       # Audio recording and playback utilities
│   ├── requirements.txt              # Dependencies for static example
│   ├── env.example                   # Environment variables
│   └── README.md                     # Static voice documentation
├── streamed/                         # Streaming voice processing example
│   ├── agent.py                      # Real-time streaming voice agent
│   ├── util.py                       # Streaming audio utilities
│   ├── requirements.txt              # Dependencies for streaming example
│   ├── env.example                   # Environment variables
│   └── README.md                     # Streaming voice documentation
├── realtime/                         # Realtime voice processing example
│   ├── agent.py                      # Basic realtime voice agent
│   ├── requirements.txt              # Dependencies for realtime example
│   ├── env.example                   # Environment variables
│   └── README.md                     # Realtime voice documentation
└── __init__.py                       # Module initialization
```

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:
- ✅ How to build complete voice interaction pipelines
- ✅ The difference between static and streaming voice processing
- ✅ How to implement multi-language voice agents with handoffs
- ✅ Best practices for voice-optimized agent design
- ✅ Real-time audio processing and streaming techniques

## 🚀 Getting Started

### **Prerequisites**

1. **Install OpenAI Agents SDK with voice support**:
   ```bash
   pip install 'openai-agents[voice]'
   ```

2. **Install audio dependencies**:
   ```bash
   pip install sounddevice numpy soundfile librosa
   ```

3. **Set up environment variables**:
   ```bash
   cp static/env.example static/.env
   cp streamed/env.example streamed/.env
   # Edit .env files and add your OpenAI API key
   ```

### **Quick Start Options**

**Option 1: Static Voice (Recommended for beginners)**
```bash
cd static/
python agent.py
```

**Option 2: Streaming Voice (Advanced)**
```bash
cd streamed/
python agent.py
```

**Option 3: Realtime Voice (Ultra-low latency)**
```bash
cd realtime/
python agent.py
```

## 🧪 Voice Agent Capabilities

### **Multi-Language Support**
Both examples include:
- **English Agent**: Primary assistant with full tool access
- **Spanish Agent**: Specialized Spanish-speaking assistant
- **French Agent**: Specialized French-speaking assistant  
- **Automatic Language Detection**: Seamless handoffs based on detected language

### **Voice-Optimized Tools**
- `get_weather(city)`: Weather information with voice-friendly responses
- `get_time()`: Current time with natural speech output
- `calculate_tip(bill, percentage)`: Tip calculations for voice queries
- `set_reminder(message, minutes)`: Voice-activated reminders (streaming only)
- `get_news_summary()`: Voice-friendly news updates (streaming only)

### **Audio Processing Features**
- **High-Quality Recording**: 24kHz audio capture
- **Real-Time Playback**: Low-latency audio output
- **Activity Detection**: Automatic speech boundary detection (streaming)
- **Error Recovery**: Robust audio pipeline error handling

## 🔧 Key Voice Agent Patterns

### **1. Basic Voice Pipeline**
```python
from agents.voice import VoicePipeline, SingleAgentVoiceWorkflow

pipeline = VoicePipeline(
    workflow=SingleAgentVoiceWorkflow(agent)
)
```

### **2. Static Audio Processing**
```python
from agents.voice import AudioInput

audio_buffer = record_audio(duration=5.0)
audio_input = AudioInput(buffer=audio_buffer)
result = await pipeline.run(audio_input)
```

### **3. Streaming Audio Processing**
```python
from agents.voice import StreamedAudioInput

streamed_input = StreamedAudioInput()
result = await pipeline.run(streamed_input)

# Push audio chunks in real-time
streamed_input.push_audio(audio_chunk)
```

### **4. Multi-Language Agent Setup**
```python
spanish_agent = Agent(
    name="Spanish",
    handoff_description="A spanish speaking agent.",
    instructions="Speak in Spanish only..."
)

main_agent = Agent(
    name="Assistant", 
    handoffs=[spanish_agent, french_agent],
    instructions="If user speaks Spanish, handoff to Spanish agent..."
)
```

## 💡 Voice Agent Best Practices

### **Agent Design for Voice**
1. **Concise Instructions**: Voice interactions work best with brief instructions
2. **Conversational Responses**: Design for natural speech patterns
3. **Clear Tool Descriptions**: Voice-friendly tool naming and descriptions
4. **Language Handling**: Implement clear language detection logic

### **Audio Quality**
1. **Good Hardware**: Use quality microphones and speakers
2. **Noise Reduction**: Minimize background noise during recording
3. **Audio Levels**: Ensure appropriate input/output volume levels
4. **Latency Optimization**: Configure audio buffers for minimal delay

### **Error Handling**
1. **Graceful Failures**: Handle audio device failures gracefully
2. **Network Issues**: Implement retry logic for API calls
3. **User Interruptions**: Allow clean exit from voice sessions
4. **Resource Cleanup**: Properly close audio streams and resources

## 🧪 Example Voice Interactions

### **English Conversations**
- "Tell me a joke" → Humorous response
- "What's the weather in London?" → Weather tool call
- "What time is it?" → Current time
- "Calculate a 18% tip on a $75 bill" → Tip calculation

### **Language Switching**  
- "Hola, ¿qué tiempo hace en Madrid?" → Spanish agent response
- "Bonjour, quelle heure est-il?" → French agent response
- Seamless language detection and agent handoffs

### **Multi-Turn Conversations (Streaming)**
- Natural back-and-forth dialogue
- Context preservation across turns
- Tool usage within conversations

## 📊 Static vs Streaming Comparison

| Feature | Static Voice | Streaming Voice |
|---------|-------------|-----------------|
| **Processing** | Turn-based | Real-time |
| **Complexity** | Simpler | More complex |
| **Latency** | Higher | Lower |
| **Use Cases** | Commands, queries | Conversations |
| **Activity Detection** | Manual | Automatic |
| **Resource Usage** | Lower | Higher |
| **User Experience** | Structured | Natural |

## 🚨 Requirements & Dependencies

### **Core Dependencies**
- `openai-agents[voice]`: Voice-enabled Agents SDK
- `sounddevice`: Real-time audio I/O
- `numpy`: Audio data processing
- `soundfile`: Audio file operations (optional)
- `librosa`: Audio resampling (optional)

### **System Requirements**
- **Python 3.8+**: Required for async support
- **Audio Hardware**: Microphone and speakers/headphones
- **Processing Power**: Sufficient CPU for real-time audio processing
- **Network**: Stable internet for OpenAI API calls

## 🔗 Related Documentation

- **[Voice Quickstart](https://openai.github.io/openai-agents-python/voice/quickstart/)**: Official voice agent setup guide
- **[Voice Pipelines](https://openai.github.io/openai-agents-python/voice/pipeline/)**: Advanced pipeline configuration
- **[Agent Fundamentals](../1_starter_agent/README.md)**: Basic agent concepts
- **[Multi-Agent Systems](../9_multi_agent_orchestration/README.md)**: Agent handoffs and orchestration

## 🚨 Troubleshooting

### **Audio Issues**
- **No microphone input**: Check audio device permissions and settings
- **Poor audio quality**: Verify microphone levels and background noise
- **Playback problems**: Test speaker/headphone configuration
- **Latency issues**: Optimize audio buffer sizes

### **Voice Pipeline Issues**
- **Transcription errors**: Ensure clear speech and good audio quality
- **Agent responses**: Verify API keys and network connectivity
- **Language detection**: Test with clear language examples
- **Handoff failures**: Check agent instructions and handoff logic

### **Performance Issues**
- **High CPU usage**: Monitor real-time processing load
- **Memory leaks**: Ensure proper cleanup of audio streams
- **Network timeouts**: Implement retry logic for API calls
- **Resource conflicts**: Check for audio device conflicts

## 💡 Pro Tips

- **Start with Static**: Master static voice processing before attempting streaming
- **Test Audio Setup**: Verify hardware configuration before development
- **Monitor Debug Output**: Use callbacks to understand pipeline behavior
- **Optimize for Voice**: Design agents specifically for conversational interaction
- **Handle Edge Cases**: Plan for network issues, audio failures, and user interruptions

## 🔗 Next Steps

After mastering voice agents:
- **Production Deployment**: Scale voice agents for real-world applications
- **Custom Voice Models**: Integrate specialized speech recognition/synthesis
- **Multi-Modal Agents**: Combine voice with vision and text capabilities
- **Enterprise Voice Solutions**: Build robust voice applications for business use
