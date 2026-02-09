# Using the Vision Agents SDK to Build a Video Agent

Build real-time video AI agents on [Stream's](https://getstream.io/video/) edge network. Process video with computer vision models, analyze frames with VLMs, or stream directly to realtime models—all with swappable providers. [Deploy to production](/guides/deployment) with [built-in metrics](/core/telemetry).

<Card title="Star Vision Agents on GitHub" icon="github" href="https://github.com/GetStream/vision-agents">
  Get started with examples, contribute, and stay updated
</Card>

<Info>
Vision Agents is provider-agnostic—bring your own API keys for [Stream](https://getstream.io/try-for-free/), LLM providers (OpenAI, Google, NVIDIA, etc.), and speech services. Most offer free tiers to get started.
</Info>

## Three Approaches

| Mode                | Best For                      | How It Works                                |
| ------------------- | ----------------------------- | ------------------------------------------- |
| **Realtime Models** | Lowest latency, native video  | WebRTC/WebSocket direct to OpenAI or Gemini |
| **VLMs**            | Video understanding, analysis | Frame buffering + chat completions API      |
| **Processors**      | Computer vision, detection    | Custom ML pipelines before the LLM          |

## Realtime Mode

Stream video directly to models with native vision support. Before we run these, please ensure you already have a fresh Python `3.12` project configured on your machine.

To get started, we'll need to add the dependencies for this project:

```bash
uv add "vision-agents[getstream,gemini,deepgram,elevenlabs]" python-dotenv
```

<Info>
For those using AI Coding tools, we recommend adding our [MCP server](https://visionagents.ai/mcp) and [Skill.md](https://visionagents.ai/skill.md) for the best experience 
</Info>

Since Vision Agents allows you to bring or reuse your existing API keys, before moving on, please ensure you create an account for the services you wish to use. We're using a few in this example; you're welcome to follow along verbatim or stick to just 1 - 2. These are loaded automatically for each plugin using `python-dotenv`.

```bash
# getstream.io API credentials
STREAM_API_KEY=your_stream_api_key_here
STREAM_API_SECRET=your_stream_api_secret_here

# Google API Key from Google AI Studio
GOOGLE_API_KEY=your_google_api_key_here

# ElevenLabs API credentials
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Deepgram API credentials
DEEPGRAM_API_KEY=your_deepgram_api_key_here
```

Next, we can move on to editing our `main.py` file with the code needed to run our `Agent` in realtime mode:

```python
from dotenv import load_dotenv

from vision_agents.core import Agent, AgentLauncher, User, Runner
from vision_agents.plugins import getstream, gemini

load_dotenv() # Automatically loads the .env

async def create_agent(**kwargs) -> Agent:
    return Agent(
        edge=getstream.Edge(),
        agent_user=User(name="Assistant", id="agent"),
        instructions="Describe what you see. Be concise.",
        llm=gemini.Realtime(fps=3),  # Video frames sent to model
    )

async def join_call(agent: Agent, call_type: str, call_id: str, **kwargs) -> None:
    call = await agent.create_call(call_type, call_id)
    async with agent.join(call):
        await agent.simple_response("What do you see?")
        await agent.finish()

if __name__ == "__main__":
    Runner(AgentLauncher(create_agent=create_agent, join_call=join_call)).cli()
```

Swap providers in one line:

```python
llm=openai.Realtime(fps=3)   # OpenAI
llm=gemini.Realtime(fps=3)   # Gemini
llm=qwen.Realtime(fps=1)     # Qwen 3 OMNI
```

## Vision Language Models (VLMs)

For video understanding and analysis, use VLMs that support the chat completions spec. Vision Agents automatically buffers frames and includes them with each request.

```python
from vision_agents.core import Agent, User
from vision_agents.plugins import nvidia, getstream, deepgram, elevenlabs

agent = Agent(
    edge=getstream.Edge(),
    agent_user=User(name="Assistant", id="agent"),
    instructions="Analyze the video and answer questions.",
    llm=nvidia.VLM(
        model="nvidia/cosmos-reason2-8b",
        fps=1,
        frame_buffer_seconds=10,
    ),
    stt=deepgram.STT(),
    tts=elevenlabs.TTS(),
)
```

Supported VLM providers:

| Provider                                     | Use Case                                            |
| -------------------------------------------- | --------------------------------------------------- |
| **[NVIDIA](/integrations/nvidia)**           | Cosmos 2 for advanced video reasoning               |
| **[HuggingFace](/integrations/huggingface)** | Open-source VLMs (Qwen2-VL, etc.) via inference API |
| **[OpenRouter](/integrations/openrouter)**   | Unified access to Claude, Gemini, and more          |

## Video Processors

For computer vision tasks like object detection, pose estimation, or custom ML models, use processors. They intercept video frames, run inference, and forward results to the LLM.

```python
from vision_agents.core import Agent, User
from vision_agents.plugins import getstream, gemini, ultralytics

agent = Agent(
    edge=getstream.Edge(),
    agent_user=User(name="Golf Coach", id="agent"),
    instructions="Analyze the user's golf swing and provide feedback.",
    llm=gemini.Realtime(fps=3),
    processors=[
        ultralytics.YOLOPoseProcessor(model_path="yolo11n-pose.pt")
    ],
)
```

Available processors:

| Processor            | What It Does                                    |
| -------------------- | ----------------------------------------------- |
| **Ultralytics YOLO** | Object detection, pose estimation, segmentation |
| **Roboflow**         | Cloud or local detection with RF-DETR           |
| **Custom**           | Extend `VideoProcessor` for any ML model        |

Processors can be chained—run detection first, then pass annotated frames to the LLM.

## Custom Pipeline

Combine VLMs with separate STT and TTS for full control:

```python
from vision_agents.core import Agent, User
from vision_agents.plugins import huggingface, getstream, deepgram, elevenlabs

agent = Agent(
    edge=getstream.Edge(),
    agent_user=User(name="Assistant", id="agent"),
    instructions="You're a visual assistant.",
    llm=huggingface.VLM(
        model="Qwen/Qwen2-VL-7B-Instruct",
        fps=1,
        frame_buffer_seconds=10,
    ),
    stt=deepgram.STT(),
    tts=elevenlabs.TTS(),
)
```

## What's Next

<CardGroup cols={2}>
  <Card title="Video Processors" icon="eye" href="/guides/video-processors">
    Build custom detection and analysis pipelines
  </Card>
  <Card title="Production Deployment" icon="server" href="/guides/deployment">
    Deploy with Docker, Kubernetes, and monitoring
  </Card>
</CardGroup>

## Examples

- [Golf Coach](https://github.com/GetStream/vision-agents/tree/main/examples/02_golf_coach_example) — Realtime pose detection + coaching
- [Security Camera](https://github.com/GetStream/vision-agents/tree/main/examples/05_security_camera_example) — Face recognition + package detection
- [Football Commentator](https://github.com/GetStream/vision-agents/tree/main/examples/04_football_commentator_example) — Object detection + live commentary
