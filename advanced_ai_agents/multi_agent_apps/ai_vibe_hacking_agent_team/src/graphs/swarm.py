from src.agents.swarm.Recon import make_recon_agent
from src.agents.swarm.InitAccess import make_initaccess_agent
from src.agents.swarm.Planner import make_planner_agent
from src.agents.swarm.Summary import make_summary_agent
from src.utils.swarm.swarm import create_swarm
from src.utils.memory import get_checkpointer, get_store
import asyncio
import logging

logger = logging.getLogger(__name__)

# 중앙 집중식 persistence 인스턴스
checkpointer = get_checkpointer()
store = get_store() 

# 비동기 함수로 workflow 선언하면 langgraph dev 는 실행안될수도있음


# 에이전트를 즉시 생성하지 않고 동적으로 생성하는 함수들로 변경
# recon = asyncio.run(make_recon_agent()) 
# initaccess = asyncio.run(make_initaccess_agent())
# planner = asyncio.run(make_planner_agent())   
# summary = asyncio.run(make_summary_agent())        

# agents = [recon, initaccess, planner, summary]

# workflow = create_swarm(
#     agents=agents,
#     default_active_agent="Planner",
# )

# swarm = workflow.compile(checkpointer=checkpointer)

# 동적 에이전트 생성 함수
async def create_agents():
    """사용자가 모델을 선택한 후 에이전트들을 동적으로 생성"""
    recon = await make_recon_agent()
    initaccess = await make_initaccess_agent()
    planner = await make_planner_agent()
    summary = await make_summary_agent()
    return [recon, initaccess, planner, summary]

async def create_dynamic_swarm():
    """동적으로 swarm 생성 - 모델 선택 후 호출"""
    logger.info("Creating dynamic swarm with InMemory persistence")
    
    agents = await create_agents()
    workflow = create_swarm(
        agents=agents,
        default_active_agent="Planner",
    )
    
    compiled_workflow = workflow.compile(
        checkpointer=checkpointer,  # ✅ InMemory 체크포인터 활성화
        store=store  # ✅ InMemory 스토어 활성화
    )
    
    logger.info("Swarm compiled with InMemory checkpointer and store")
    return compiled_workflow
