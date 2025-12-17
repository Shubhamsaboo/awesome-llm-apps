from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import google_search

# --- Sub-agents ---
research_agent = LlmAgent(
    name="research_agent",
    model="gemini-3-flash-preview",
    description="Finds key information and outlines for a given topic.",
    instruction=(
        "You are a focused research specialist. Given a user topic or goal, "
        "conduct thorough research and produce:\n"
        "1. A comprehensive bullet list of key facts and findings\n"
        "2. Relevant sources and references (when available)\n"
        "3. A structured outline for approaching the topic\n"
        "4. Current trends or recent developments\n\n"
        "Keep your research factual, well-organized, and comprehensive. "
        "Use the google_search tool to find current information when needed."
    ),
    tools=[google_search]
)

summarizer_agent = LlmAgent(
    name="summarizer_agent",
    model="gemini-3-flash-preview",
    description="Summarizes research findings clearly and concisely.",
    instruction=(
        "You are a skilled summarizer. Given research findings, create:\n"
        "1. A concise executive summary (2-3 sentences)\n"
        "2. 5-7 key bullet points highlighting the most important information\n"
        "3. A clear takeaway message\n"
        "4. Any critical insights or patterns you notice\n\n"
        "Focus on clarity, relevance, and actionable insights. "
        "Avoid repetition and maintain the logical flow of information."
    ),
)

critic_agent = LlmAgent(
    name="critic_agent",
    model="gemini-3-flash-preview",
    description="Provides constructive critique and improvement suggestions.",
    instruction=(
        "You are a thoughtful analyst and critic. Given research and summaries, provide:\n"
        "1. **Gap Analysis**: Identify missing information or areas that need more research\n"
        "2. **Risk Assessment**: Highlight potential risks, limitations, or biases\n"
        "3. **Opportunity Identification**: Suggest areas for further exploration or improvement\n"
        "4. **Quality Score**: Rate the overall research quality (1-10) with justification\n"
        "5. **Actionable Recommendations**: Provide specific next steps or improvements\n\n"
        "Be constructive, thorough, and evidence-based in your analysis."
    ),
)

# --- Coordinator (root) agent ---
root_agent = LlmAgent(
    name="multi_agent_researcher",
    model="gemini-3-flash-preview",
    description="Advanced multi-agent research coordinator that orchestrates research, analysis, and critique.",
    instruction=(
        "You are an advanced research coordinator managing a team of specialized agents.\n\n"
        "**Your Research Team:**\n"
        "- **research_agent**: Conducts comprehensive research using web search and analysis\n"
        "- **summarizer_agent**: Synthesizes findings into clear, actionable insights\n"
        "- **critic_agent**: Provides quality analysis, gap identification, and recommendations\n\n"
        "**Research Workflow:**\n"
        "1. **Research Phase**: Delegate to research_agent to gather comprehensive information\n"
        "2. **Synthesis Phase**: Use summarizer_agent to distill findings into key insights\n"
        "3. **Analysis Phase**: Engage critic_agent to evaluate quality and identify opportunities\n"
        "4. **Integration**: Combine all outputs into a cohesive research report\n\n"
        "**For Each Research Request:**\n"
        "- Always start with research_agent to gather information\n"
        "- Then use summarizer_agent to create clear summaries\n"
        "- Finally, engage critic_agent for quality analysis and recommendations\n"
        "- Present the final integrated research report to the user\n\n"
        "**Output Format:**\n"
        "Provide a structured response that includes:\n"
        "- Executive Summary\n"
        "- Key Findings\n"
        "- Critical Analysis\n"
        "- Recommendations\n"
        "- Next Steps\n\n"
        "Coordinate your team effectively to deliver high-quality, comprehensive research."
    ),
    sub_agents=[summarizer_agent, critic_agent],
    tools=[AgentTool(research_agent)]
)