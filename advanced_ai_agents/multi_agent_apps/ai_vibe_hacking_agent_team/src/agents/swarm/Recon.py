from langgraph.prebuilt import create_react_agent
from src.prompts.prompt_loader import load_prompt
from src.tools.handoff import handoff_to_planner, handoff_to_initial_access, handoff_to_summary
from langchain_mcp_adapters.client import MultiServerMCPClient
from langmem import create_manage_memory_tool, create_search_memory_tool
from src.utils.llm.config_manager import get_current_llm
from src.utils.memory import get_store 

from src.utils.mcp.mcp_loader import load_mcp_tools

async def make_recon_agent():
    # reconnaissance 서버만 MCP 도구 로드
    # 메모리에서 LLM 로드 (없으면 기본값 사용)
    llm = get_current_llm()
    if llm is None:
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model_name="claude-3-5-sonnet-latest", temperature=0, timeout=60, stop=None)
        print("Warning: Using default LLM model (Claude 3.5 Sonnet)")
    
    # 중앙 집중식 store 사용
    store = get_store()
    
    mcp_tools = await load_mcp_tools(agent_name=["reconnaissance"])
    swarm_tools = [
        handoff_to_initial_access,
        handoff_to_planner,
        handoff_to_summary,
    ]

    mem_tools = [
        create_manage_memory_tool(namespace=("memories",)),
        create_search_memory_tool(namespace=("memories",))
    ]

        
    tools = mcp_tools + swarm_tools + mem_tools
        
    
    agent = create_react_agent(
        llm,
        tools=tools,
        store=store,
        name="Reconnaissance",
        prompt=load_prompt("reconnaissance", "swarm")
    )
    return agent