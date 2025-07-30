# base terminal management
from src.prompts.base.terminal import BASE_TERMINAL_PROMPT

# personas
from src.prompts.personas.reconnaissance_persona import RECONNAISSANCE_PERSONA_PROMPT
from src.prompts.personas.initial_access_persona import INITIAL_ACCESS_PERSONA_PROMPT
from src.prompts.personas.planner_persona import PLANNER_PERSONA_PROMPT
from src.prompts.personas.summary_persona import SUMMARY_PERSONA_PROMPT
from src.prompts.personas.supervisor_persona import SUPERVISOR_PERSONA_PROMPT

# swarm coordination
from src.prompts.swarm.summary import SWARM_SUMMARY_PROMPT
from src.prompts.swarm.planner import SWARM_PLANNER_PROMPT
from src.prompts.swarm.recon import SWARM_RECON_PROMPT
from src.prompts.swarm.initaccess import SWARM_INITACCESS_PROMPT

# additional tools
from src.prompts.tools.swarm_handoff_tools import SWARM_HANDOFF_TOOLS_PROMPT

# 에이전트 타입과 프롬프트 매핑
PERSONA_PROMPTS = {
    "reconnaissance": RECONNAISSANCE_PERSONA_PROMPT,
    "initial_access": INITIAL_ACCESS_PERSONA_PROMPT,
    "planner": PLANNER_PERSONA_PROMPT,
    "summary": SUMMARY_PERSONA_PROMPT,
    "supervisor": SUPERVISOR_PERSONA_PROMPT
}

SWARM_PROMPTS = {
    "reconnaissance": SWARM_RECON_PROMPT,
    "initial_access": SWARM_INITACCESS_PROMPT,
    "planner": SWARM_PLANNER_PROMPT,
    "summary": SWARM_SUMMARY_PROMPT,
    "supervisor": ""  # Supervisor는 swarm 전용 프롬프트 없음
}

def load_prompt(agent_name: str, architecture: str = "swarm"):
    """
    통합 프롬프트 로더 - 모든 에이전트의 프롬프트를 로드
    
    Args:
        agent_name: "reconnaissance", "initial_access", "planner", "summary", "supervisor"
        architecture: "swarm", "hierarchical", "standalone"
    
    Returns:
        완성된 에이전트 프롬프트
        
    Examples:
        load_prompt("reconnaissance", "swarm")
        load_prompt("initial_access", "standalone") 
        load_prompt("supervisor", "hierarchical")
    """
    if agent_name not in PERSONA_PROMPTS:
        available_agents = list(PERSONA_PROMPTS.keys())
        raise ValueError(f"Unknown agent: {agent_name}. Available agents: {available_agents}")
    
    # 기본 구조: 터미널 + 페르소나
    prompt = BASE_TERMINAL_PROMPT + PERSONA_PROMPTS[agent_name]
    
    # Swarm 아키텍처인 경우 추가 기능
    if architecture == "swarm" and agent_name != "supervisor":
        swarm_prompt = SWARM_PROMPTS.get(agent_name, "")
        if swarm_prompt:
            prompt += swarm_prompt
        prompt += SWARM_HANDOFF_TOOLS_PROMPT
    
    return prompt

def get_available_agents():
    """사용 가능한 에이전트 목록 반환"""
    return list(PERSONA_PROMPTS.keys())

def get_supported_architectures():
    """지원되는 아키텍처 목록 반환"""
    return ["swarm", "hierarchical", "standalone"]

def get_terminal_base_prompt():
    """터미널 기본 프롬프트만 반환 (디버깅/테스트용)"""
    return BASE_TERMINAL_PROMPT
