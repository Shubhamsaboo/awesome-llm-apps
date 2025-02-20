import asyncio
import streamlit as st
from autogen import (
    SwarmAgent,
    SwarmResult,
    initiate_swarm_chat,
    OpenAIWrapper,
    AFTER_WORK,
    UPDATE_SYSTEM_MESSAGE
)
import agentops
import os
from contextlib import contextmanager

# Add this at the top of the file, before any other code
os.environ["AUTOGEN_USE_DOCKER"] = "0"

# Initialize session state
if 'output' not in st.session_state:
    st.session_state.output = {
        'climate': '',
        'urban': '',
        'economic': '',
        'community': ''
    }

# Sidebar for API key input
st.sidebar.title("OpenAI API Key")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")

st.sidebar.title("AgentOps API Key")
agentops_key = st.sidebar.text_input("Enter your AgentOps API Key", type="password", value="4e725ba8-b57e-49b5-809a-4eeef18d92ed")

# Main app UI
st.title("🌍 Climate Impact Response Planner")

# Add agent information below title
st.info("""
**Meet Your Climate Planning Team:**

🌡️ **Climate Analysis Agent** - Analyzes climate data and risk projections
🏙️ **Urban Planning Agent** - Develops infrastructure and zoning strategies
💰 **Economic Impact Agent** - Assesses financial implications
👥 **Community Engagement Agent** - Plans public involvement and behavior change
""")

# User input
st.subheader("City Information")
city_name = st.text_input("Enter City Name", "")
city_description = st.text_area("Brief description of the city (population, geography, main industries, etc.)", "")

@contextmanager
def agentops_session(api_key: str, tags: list):
    """Context manager for AgentOps sessions"""
    try:
        # Initialize new session
        agentops.init(
            api_key=api_key,
            tags=tags,
            instrument_llm_calls=True,
            auto_start_session=True
        )
        yield
    finally:
        # Always ensure session is ended
        try:
            agentops.end_session("Success")
        except Exception as e:
            print(f"Failed to end AgentOps session: {e}")

# Button to start the agent collaboration
if st.button("Generate Climate Response Plan"):
    if not api_key:
        st.error("Please enter your OpenAI API key.")
    else:
        with st.spinner('🤖 AI Agents are collaborating on your climate response plan...'):
            with agentops_session(api_key=agentops_key, tags=["aqi_agent"]):
                try:
                    task = f"""
                    Create a comprehensive climate impact response plan for:
                    City: {city_name}
                    Description: {city_description}
                    
                    Consider all aspects of climate adaptation including environmental, infrastructural, economic, and social factors.
                    """

                    # Then modify the agent configurations
                    llm_config = {
                        "config_list": [{"model": "gpt-4o", "api_key": api_key}]
                    }

                    # Context management for agent communication
                    context_variables = {
                        "climate": None,
                        "urban": None,
                        "economic": None,
                        "community": None,
                    }

                    # Update functions for each agent
                    def update_climate_overview(climate_summary: str, context_variables: dict) -> SwarmResult:
                        """Keep the summary as short as possible."""
                        context_variables["climate"] = climate_summary
                        st.sidebar.success('Climate Analysis: ' + climate_summary)
                        return SwarmResult(agent="urban_agent", context_variables=context_variables)
                        
                    def update_urban_overview(urban_summary: str, context_variables: dict) -> SwarmResult:
                        """Keep the summary as short as possible."""
                        context_variables["urban"] = urban_summary
                        st.sidebar.success('Urban Planning: ' + urban_summary)
                        return SwarmResult(agent="economic_agent", context_variables=context_variables)

                    def update_economic_overview(economic_summary: str, context_variables: dict) -> SwarmResult:
                        """Keep the summary as short as possible."""
                        context_variables["economic"] = economic_summary
                        st.sidebar.success('Economic Impact: ' + economic_summary)
                        return SwarmResult(agent="community_agent", context_variables=context_variables)

                    def update_community_overview(community_summary: str, context_variables: dict) -> SwarmResult:
                        """Keep the summary as short as possible."""
                        context_variables["community"] = community_summary
                        st.sidebar.success('Community Engagement: ' + community_summary)
                        return SwarmResult(agent="climate_agent", context_variables=context_variables)

                    system_messages = {
                        "climate_agent": """
                        You are an expert climate scientist and risk analyst. Your task is to:
                        1. Analyze historical climate data and future projections for the specified city
                        2. Identify key climate risks (flooding, heat waves, storms, etc.)
                        3. Assess vulnerability of different city areas and systems
                        4. Prioritize climate threats based on likelihood and impact
                        5. Recommend key areas for climate resilience focus
                        6. Provide specific climate scenarios the city should prepare for
                        """,
                        
                        "urban_agent": """
                        You are an experienced urban planner specializing in climate adaptation. Your task is to:
                        1. Design infrastructure modifications for climate resilience
                        2. Develop zoning recommendations for risk reduction
                        3. Plan green infrastructure and nature-based solutions
                        4. Identify critical infrastructure vulnerabilities
                        5. Create phased implementation strategies
                        6. Consider both immediate and long-term adaptation needs
                        """,
                        
                        "economic_agent": """
                        You are a climate economics and finance specialist. Your task is to:
                        1. Calculate potential economic impacts of climate risks
                        2. Identify funding sources for adaptation projects
                        3. Analyze cost-benefit ratios of proposed solutions
                        4. Assess impacts on local industries and businesses
                        5. Develop economic incentives for climate adaptation
                        6. Create budget allocation recommendations
                        """,
                        
                        "community_agent": """
                        You are a community engagement and behavior change expert. Your task is to:
                        1. Design public communication strategies
                        2. Plan community involvement in adaptation efforts
                        3. Develop education and awareness programs
                        4. Create behavior change initiatives
                        5. Plan vulnerable population support systems
                        6. Design feedback and monitoring systems
                        """
                    }

                    def update_system_message_func(agent: SwarmAgent, messages) -> str:
                        """"""
                        system_prompt = system_messages[agent.name]

                        current_gen = agent.name.split("_")[0]
                        if agent._context_variables.get(current_gen) is None:
                            system_prompt += f"Call the update function provided to first provide a 2-3 sentence summary of your ideas on {current_gen.upper()} based on the context provided."
                            agent.llm_config['tool_choice'] = {"type": "function", "function": {"name": f"update_{current_gen}_overview"}}
                            agent.client = OpenAIWrapper(**agent.llm_config)
                        else:
                            # remove the tools to avoid the agent from using it and reduce cost
                            agent.llm_config["tools"] = None
                            agent.llm_config['tool_choice'] = None
                            agent.client = OpenAIWrapper(**agent.llm_config)
                            # the agent has given a summary, now it should generate a detailed response
                            system_prompt += f"\n\nYour task\nYou task is write the {current_gen} part of the report. Do not include any other parts. Do not use XML tags.\nStart your reponse with: '## {current_gen.capitalize()} Design'."    
                            
                            # Remove all messages except the first one with less cost
                            k = list(agent._oai_messages.keys())[-1]
                            agent._oai_messages[k] = agent._oai_messages[k][:1]

                        system_prompt += f"\n\n\nBelow are some context for you to refer to:"
                        # Add context variables to the prompt
                        for k, v in agent._context_variables.items():
                            if v is not None:
                                system_prompt += f"\n{k.capitalize()} Summary:\n{v}"

                        return system_prompt
                    
                    state_update = UPDATE_SYSTEM_MESSAGE(update_system_message_func)

                    # Define agents with proper code execution config
                    climate_agent = SwarmAgent(
                        "climate_agent", 
                        llm_config=llm_config,
                        functions=update_climate_overview,
                        update_agent_state_before_reply=[state_update]
                    )

                    urban_agent = SwarmAgent(
                        "urban_agent",
                        llm_config=llm_config,
                        functions=update_urban_overview,
                        update_agent_state_before_reply=[state_update]
                    )

                    economic_agent = SwarmAgent(
                        "economic_agent",
                        llm_config=llm_config,
                        functions=update_economic_overview,
                        update_agent_state_before_reply=[state_update]
                    )

                    community_agent = SwarmAgent(
                        name="community_agent",
                        llm_config=llm_config,
                        functions=update_community_overview,
                        update_agent_state_before_reply=[state_update]
                    )

                    climate_agent.register_hand_off(AFTER_WORK(urban_agent))
                    urban_agent.register_hand_off(AFTER_WORK(economic_agent))
                    economic_agent.register_hand_off(AFTER_WORK(community_agent))
                    community_agent.register_hand_off(AFTER_WORK(climate_agent))

                    result, _, _ = initiate_swarm_chat(
                        initial_agent=climate_agent,
                        agents=[climate_agent, urban_agent, economic_agent, community_agent],
                        user_agent=None,
                        messages=task,
                        max_rounds=13,
                    )

                    # Update session state with the individual responses
                    st.session_state.output = {
                        'climate': result.chat_history[-4]['content'],
                        'urban': result.chat_history[-3]['content'],
                        'economic': result.chat_history[-2]['content'],
                        'community': result.chat_history[-1]['content']
                    }

                    # Display success message after completion
                    st.success('✨ Climate response plan generated successfully!')

                    # Display the individual outputs in expanders
                    with st.expander("Climate Analysis"):
                        st.markdown(st.session_state.output['climate'])

                    with st.expander("Urban Planning"):
                        st.markdown(st.session_state.output['urban'])

                    with st.expander("Economic Impact"):
                        st.markdown(st.session_state.output['economic'])

                    with st.expander("Community Engagement"):
                        st.markdown(st.session_state.output['community'])

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    raise  # Re-raise to trigger session end with error
