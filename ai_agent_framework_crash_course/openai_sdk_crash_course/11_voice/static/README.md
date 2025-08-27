# 🎙️ Static Voice Agent

A complete voice interaction example using the OpenAI Agents SDK with pre-recorded audio input. This demonstrates the basic voice pipeline workflow with speech-to-text, agent processing, and text-to-speech capabilities.

## 🎯 What This Demonstrates

- **Static Audio Processing**: Record once, process completely
- **Voice Pipeline**: Complete speech-to-text → agent → text-to-speech workflow
- **Multi-Agent System**: Agent handoffs based on language detection
- **Tool Integration**: Voice-activated tools for weather, time, and calculations
- **Audio Management**: Recording, playback, and audio utility functions

## 🧠 Core Concept: Static Voice Pipeline

The static voice pipeline processes a complete audio recording in one workflow. Think of it as a **turn-based voice assistant** that:

- Records your complete message first
- Transcribes the entire audio to text
- Processes with AI agents and tools
- Converts the complete response back to speech
- Plays the full audio response

```
┌─────────────────────────────────────────────────────────────┐
│                    STATIC VOICE WORKFLOW                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🎤 RECORD AUDIO                                            |
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    1. COMPLETE RECORDING                   │
│  │   AUDIO     │    ◦ Record for fixed duration             │
│  │  CAPTURE    │    ◦ Full audio buffer                     │
│  └─────────────┘                                            │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    2. SPEECH-TO-TEXT                       │
│  │ TRANSCRIBE  │    ◦ Convert full audio to text            │
│  │   AUDIO     │    ◦ Complete transcription                │
│  └─────────────┘                                            │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    3. AGENT PROCESSING                     │
│  │   AGENT     │    ◦ Multi-agent workflow                  │
│  │ WORKFLOW    │    ◦ Tool calls & handoffs                 │
│  └─────────────┘                                            │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    4. TEXT-TO-SPEECH                       │
│  │  GENERATE   │    ◦ Convert response to audio             │
│  │   SPEECH    │    ◦ Stream audio output                   │
│  └─────────────┘                                            │
│       │                                                     │
│       ▼                                                     │
│  🔊 PLAY RESPONSE                                           │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

1. **Install voice dependencies**:
   ```bash
   pip install 'openai-agents[voice]'
   pip install sounddevice numpy soundfile librosa
   ```

2. **Set up environment**:
   ```bash
   cp env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Run the static voice agent**:
   ```bash
   python agent.py
   ```

## 🧪 What This Example Includes

### **Multi-Language Support**
- **English Agent**: Primary assistant with all tools
- **Spanish Agent**: Specialized Spanish-speaking agent 
- **French Agent**: Specialized French-speaking agent
- **Automatic Language Detection**: Handoffs based on detected language

### **Voice-Activated Tools**
- `get_weather(city)`: Get weather information for any city
- `get_time()`: Get current time
- `calculate_tip(bill, percentage)`: Calculate tips for bills

### **Audio Utilities**
- `AudioPlayer`: Real-time audio playback with sounddevice
- `record_audio()`: Microphone recording with duration control
- `create_silence()`: Generate silence buffers
- `save_audio()` / `load_audio()`: Audio file operations

### **Workflow Callbacks**
- `WorkflowCallbacks`: Monitor transcription, tool calls, and handoffs
- Debug output for pipeline monitoring
- Performance tracking and statistics

## 🎯 Example Interactions

### **English Examples**
- "Tell me a joke" → Agent responds with humor
- "What's the weather in Tokyo?" → Calls weather tool
- "What time is it?" → Calls time tool
- "Calculate a 20% tip on a $50 bill" → Performs calculation

### **Language Handoffs**
- "Hola, ¿cómo estás?" → Handoff to Spanish agent
- "Bonjour, comment allez-vous?" → Handoff to French agent
- Agents respond in the detected language

### **Tool Integration**
- Weather queries work in any language
- Time and calculation tools available to all agents
- Tools called automatically based on user requests

## 🔧 Key Implementation Patterns

### **1. Voice Pipeline Setup**
```python
pipeline = VoicePipeline(
    workflow=SingleAgentVoiceWorkflow(agent, callbacks=WorkflowCallbacks())
)
```

### **2. Audio Input Processing**
```python
audio_buffer = record_audio(duration=5.0)
audio_input = AudioInput(buffer=audio_buffer)
result = await pipeline.run(audio_input)
```

### **3. Audio Output Streaming**
```python
with AudioPlayer() as player:
    async for event in result.stream():
        if event.type == "voice_stream_event_audio":
            player.add_audio(event.data)
```

### **4. Multi-Agent Configuration**
```python
agent = Agent(
    name="Assistant",
    handoffs=[spanish_agent, french_agent],
    tools=[get_weather, get_time, calculate_tip]
)
```

## 💡 Voice Agent Best Practices

1. **Clear Audio Recording**: Ensure good microphone quality and minimal background noise
2. **Concise Instructions**: Voice interactions work best with brief, clear agent instructions
3. **Error Handling**: Implement robust error handling for audio recording failures
4. **Language Detection**: Use prompt engineering for automatic language switching
5. **Tool Design**: Design tools for voice interaction with conversational responses

## 📊 Performance Characteristics

### **Static Pipeline Benefits**
- **Predictable Processing**: Fixed recording duration
- **Complete Context**: Full utterance available for processing
- **Simpler Implementation**: No real-time complexity
- **Better for Complex Queries**: Can process longer, detailed requests

### **Use Cases**
- **Voice Assistants**: Traditional turn-based interaction
- **Voice Commands**: Specific task automation
- **Language Learning**: Practice with multilingual agents
- **Accessibility**: Voice interface for applications

## 🚨 Requirements & Dependencies

### **Core Dependencies**
- `openai-agents[voice]`: OpenAI Agents SDK with voice support
- `sounddevice`: Audio recording and playback
- `numpy`: Audio data processing
- `soundfile`: Audio file operations (optional)
- `librosa`: Audio resampling (optional)

### **System Requirements**
- **Microphone**: For audio input
- **Speakers/Headphones**: For audio output
- **Python 3.8+**: Required for async support

## 🔗 Related Examples

- **[Streaming Voice](../streamed/README.md)**: Real-time voice interaction
- **[Voice Pipeline Documentation](https://openai.github.io/openai-agents-python/voice/pipeline/)**: Official pipeline docs
- **[Voice Quickstart](https://openai.github.io/openai-agents-python/voice/quickstart/)**: Basic voice setup

## 🛠️ Customization Options

### **Extend Audio Utilities**
- Add audio effects and filtering
- Implement custom audio formats
- Add audio visualization

### **Enhance Agent Capabilities**
- Add more specialized language agents
- Implement domain-specific tools
- Add conversation memory

### **Improve Voice Experience**
- Add voice activity detection
- Implement custom wake words
- Add voice emotion detection

## 💡 Pro Tips

- **Test Audio Setup**: Verify microphone and speakers before running
- **Experiment with Duration**: Adjust recording duration based on use case
- **Monitor Debug Output**: Use callbacks to understand pipeline behavior
- **Handle Interruptions**: Implement graceful handling of Ctrl+C
- **Optimize for Voice**: Keep agent responses concise and conversational

## 🔗 Next Steps

After mastering static voice agents:
- **[Streaming Voice](../streamed/README.md)**: Implement real-time voice interaction
- **[Advanced Voice Pipelines](https://openai.github.io/openai-agents-python/voice/pipeline/)**: Custom pipeline configurations
- **Production Voice Apps**: Deploy voice agents in real applications
