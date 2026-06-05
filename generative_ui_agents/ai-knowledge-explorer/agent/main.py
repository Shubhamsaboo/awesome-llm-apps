from copilotkit import CopilotKitMiddleware
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from src.state import AgentState
from src.tools import knowledge_tools

model = ChatOpenAI(model="gpt-5.5", model_kwargs={"parallel_tool_calls": False})

agent = create_agent(
    model=model,
    tools=knowledge_tools,
    middleware=[
        CopilotKitMiddleware(),
    ],
    state_schema=AgentState,
    system_prompt="""You are a knowledge explorer agent that works with both documents and source code.

RULES:
1. When a user uploads files or asks to build a graph, call extract_knowledge. Do NOT extract entities yourself.
2. Only call find_connections when the user explicitly asks for deeper connections.
3. When asked to expand a node, call expand_node with the node_id.
4. NEVER output JSON or structured data. That is the tool's job.
5. Keep responses to 1-2 sentences. The graph does the talking.
6. If you feel tempted to list entities or output JSON — STOP and call the tool instead.

After extraction completes, say something brief like "Mapped X concepts and Y connections. Click any node to explore."

When the user says they uploaded files, call extract_knowledge immediately.
""",
)

graph = agent
