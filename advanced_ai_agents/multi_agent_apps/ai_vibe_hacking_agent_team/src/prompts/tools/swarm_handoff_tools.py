"""
Swarm 아키텍처용 handoff 도구 프롬프트

이 파일은 Swarm 아키텍처에서 에이전트 간 작업 전환을 위한 도구에 대한 프롬프트를 정의합니다.
"""

SWARM_HANDOFF_TOOLS_PROMPT = """
<swarm_handoff_tools>
## Agent Handoff Tools:

### transfer_to_Planner(task_description)
**When to use**: Need strategic planning, analysis, or tactical guidance
**Examples**: 
- Initial mission planning
- Strategy adjustment after obstacles
- Complex intelligence analysis

### transfer_to_Reconnaissance(task_description)  
**When to use**: Need specialized intelligence gathering or target enumeration
**Examples**:
- Deep service enumeration
- Network expansion discovery
- Verification of findings

### transfer_to_Initial_Access(task_description)
**When to use**: Ready for exploitation or credential attacks
**Examples**:
- Vulnerability exploitation campaign
- Authentication bypass attempts
- Post-reconnaissance exploitation

### transfer_to_Summary(task_description)
**When to use**: Need documentation of findings or phase completion
**Examples**:
- Phase completion reporting
- Critical finding documentation
- Final engagement summary

## Handoff Best Practices:
- Provide clear context and objectives
- Include all relevant findings and data
- Specify expected deliverables
- Maintain mission continuity

Use handoffs to leverage specialized expertise while maintaining operational flow.
</swarm_handoff_tools>
"""
