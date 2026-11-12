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

# 1. Dummy tool that intentionally fails to simulate a silent loop
@tool
def fetch_server_status(server_id: str) -> str:
    """Fetches the status of a specific server."""
    return f"Error: Connection timeout while reaching {server_id}. Please try again."

tools = [fetch_server_status]
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0).bind_tools(tools)

# 2. Agent State to track messages and recent tool calls
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    tool_history: List[str]

# 3. Agent Node
def agent_node(state: AgentState):
    response = llm.invoke(state["messages"])
    new_history = list(state.get("tool_history", []))
    
    if response.tool_calls:
        for tc in response.tool_calls:
            call_signature = f"{tc['name']}:{tc['args']}"
            new_history.append(call_signature)
            
    return {"messages": [response], "tool_history": new_history}

# 4. Self-Healing / Loop-Detection Middleware Node
def loop_detector_node(state: AgentState):
    history = state.get("tool_history", [])
    
    # Check if the last 3 tool calls are identical
    if len(history) >= 3 and len(set(history[-3:])) == 1:
        repeated_action = history[-1]
        
        # Trigger interrupt to halt execution and ask for human guidance
        user_guidance = interrupt(
            f"\n🚨 [LOOP DETECTED]: The agent repeated '{repeated_action}' 3 times in a row!\n"
            f"Execution paused to save API credits. How should the agent proceed? "
        )
        
        return {
            "messages": [HumanMessage(content=f"Admin Intervention: {user_guidance}")],
            "tool_history": [] 
        }
    
    return {}

# 5. Routing Logic
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "loop_detector"
    return END

# 6. Build the LangGraph workflow
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("loop_detector", loop_detector_node)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, ["loop_detector", END])
workflow.add_edge("loop_detector", "tools")
workflow.add_edge("tools", "agent")

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# 7. Run the live demonstration
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "demo-thread-1"}}
    print("🤖 Starting agent execution...\n")
    
    initial_input = {
        "messages": [HumanMessage(content="Check the status of 'prod-db-01'. Keep trying until it works.")],
        "tool_history": []
    }
    
    for event in app.stream(initial_input, config, stream_mode="values"):
        if "messages" in event:
            last_msg = event["messages"][-1]
            if last_msg.type == "ai" and last_msg.tool_calls:
                print(f"🔄 Agent Calling Tool: {last_msg.tool_calls['name']} with {last_msg.tool_calls['args']}")

    state_snapshot = app.get_state(config)
    if state_snapshot.next:
        interrupt_msg = state_snapshot.tasks.interrupts.value
        user_reply = input(interrupt_msg)
        
        print("\n✅ Resuming agent with user instructions...\n")
        for event in app.stream(Command(resume=user_reply), config, stream_mode="values"):
            if "messages" in event:
                last_msg = event["messages"][-1]
                if last_msg.type == "ai" and not last_msg.tool_calls:
                    print(f"🤖 Final Response: {last_msg.content}")
