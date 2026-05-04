"""
Entry point for the Open Generative UI demo agent.

The agent itself stays minimal — Open Generative UI is enabled by the
`@copilotkit/runtime` middleware on the Next.js side (see
`src/app/api/copilotkit/[[...slug]]/route.ts`). That middleware injects a
`generateSandboxedUi` tool the model can call to stream HTML / CSS / JS into a
sandboxed iframe in the chat. No special agent-side wiring is required.
"""

from copilotkit import CopilotKitMiddleware
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from src.query import query_data

model = ChatOpenAI(model="gpt-5.4-mini", model_kwargs={"parallel_tool_calls": False})

agent = create_agent(
    model=model,
    tools=[query_data],
    middleware=[CopilotKitMiddleware()],
    system_prompt="""
        You are a demo assistant for Open Generative UI. Keep responses to 1-2 sentences
        unless the user asks for more.

        Tool guidance:
        - When the user asks for a visual, dashboard, animation, diagram, mini-app, or
          interactive component, call the `generateSandboxedUi` tool. The runtime streams
          the generated HTML / CSS / JS into a sandboxed iframe live in the chat.
        - When the visual needs real numbers (charts, KPI cards, tables), call
          `query_data` first to fetch sample data, then pass that data along when calling
          `generateSandboxedUi`.
        - For plain Q&A or chit-chat, do not call any tool — just answer in chat.
    """,
)

graph = agent
