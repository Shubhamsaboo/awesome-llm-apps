import os
from typing import Annotated, TypedDict, List
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command


# 1. Dummy tool jo fail hoga (loop simulate karne ke liye)
@tool
def fetch_server_status(server_id: str) -> str:
    """Fetches the status of a specific server."""
    return f"Error: Connection timeout while reaching {server_id}. Please try again."


tools = [fetch_server_status]
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0).bind_tools(tools)


# 2. Agent State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    tool_history: List[str]
    loop_triggered: bool


# 3. Agent Node
def agent_node(state: AgentState):
    response = llm.invoke(state["messages"])
    new_history = list(state.get("tool_history", []))

    if response.tool_calls:
        for tc in response.tool_calls:
            call_signature = f"{tc['name']}:{tc['args']}"
            new_history.append(call_signature)

    return {
        "messages": [response],
        "tool_history": new_history,
        "loop_triggered": False,
    }


# 4. Loop-Detection Node
def loop_detector_node(state: AgentState):
    history = state.get("tool_history", [])

    if len(history) >= 3 and len(set(history[-3:])) == 1:
        repeated_action = history[-1]

        user_guidance = interrupt(
            f"\n🚨 [LOOP DETECTED]: Agent repeated '{repeated_action}' 3 times in a row!\n"
            f"Execution paused to save API credits. How should the agent proceed? "
        )

        return {
            "messages": [HumanMessage(content=f"Admin Intervention: {user_guidance}")],
            "tool_history": [],
            "loop_triggered": True,
        }

    return {"loop_triggered": False}


# 5. Routing after agent node
def route_after_agent(state: AgentState):
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "loop_detector"
    return END


# 6. Routing after loop_detector node — key fix:
#    agar loop trigger hua (admin ne guidance di) -> wapas agent pe jao
#    agar normal hai -> tools call karo
def route_after_loop_detector(state: AgentState):
    if state.get("loop_triggered"):
        return "agent"
    return "tools"


# 7. Build graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("loop_detector", loop_detector_node)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    route_after_agent,
    {"loop_detector": "loop_detector", END: END},
)

workflow.add_conditional_edges(
    "loop_detector",
    route_after_loop_detector,
    {"agent": "agent", "tools": "tools"},
)

workflow.add_edge("tools", "agent")

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)


# 8. Run demo
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "demo-thread-1"}}
    print("🤖 Starting agent execution...\n")

    initial_input = {
        "messages": [
            HumanMessage(
                content="Check the status of 'prod-db-01'. Keep trying until it works."
            )
        ],
        "tool_history": [],
        "loop_triggered": False,
    }

    for event in app.stream(initial_input, config, stream_mode="values"):
        if "messages" in event:
            last_msg = event["messages"][-1]
            if last_msg.type == "ai" and last_msg.tool_calls:
                for tc in last_msg.tool_calls:
                    print(f"🔄 Agent Calling Tool: {tc['name']} with {tc['args']}")

    state_snapshot = app.get_state(config)

    while state_snapshot.next:
        interrupt_obj = state_snapshot.tasks[0].interrupts[0]
        user_reply = input(interrupt_obj.value)

        print("\n✅ Resuming agent with user instructions...\n")
        for event in app.stream(Command(resume=user_reply), config, stream_mode="values"):
            if "messages" in event:
                last_msg = event["messages"][-1]
                if last_msg.type == "ai" and not last_msg.tool_calls:
                    print(f"🤖 Final Response: {last_msg.content}")

        state_snapshot = app.get_state(config)

    print("\n✅ Agent execution finished.")