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
        'psychology': '',
        'resources': '',
        'action': '',
        'followup': ''
    }

# Sidebar for API key input
st.sidebar.title("OpenAI API Key")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")

st.sidebar.title("AgentOps API Key")
agentops_key = st.sidebar.text_input("Enter your AgentOps API Key", type="password", value="4e725ba8-b57e-49b5-809a-4eeef18d92ed")

# Main app UI
st.title("🧠 Mental Health Crisis Navigator")

# Add agent information below title
st.info("""
**Meet Your Mental Health Support Team:**

🧠 **Psychology Agent** - Analyzes emotional state and psychological needs
📋 **Resource Agent** - Identifies relevant support services and professionals
🎯 **Action Agent** - Creates immediate step-by-step action plans
🔄 **Follow-up Agent** - Designs ongoing support and prevention strategies
""")

# User inputs
st.subheader("Personal Information")
col1, col2 = st.columns(2)

with col1:
    mental_state = st.text_area("How have you been feeling recently?", 
        placeholder="Describe your emotional state, thoughts, or concerns...")
    sleep_pattern = st.select_slider(
        "Sleep Pattern (hours per night)",
        options=[f"{i}" for i in range(0, 13)],
        value="7"
    )
    
with col2:
    stress_level = st.slider("Current Stress Level (1-10)", 1, 10, 5)
    support_system = st.multiselect(
        "Current Support System",
        ["Family", "Friends", "Therapist", "Support Groups", "None"]
    )

# Additional context
recent_changes = st.text_area(
    "Any significant life changes or events recently?",
    placeholder="Job changes, relationships, losses, etc..."
)

current_symptoms = st.multiselect(
    "Current Symptoms",
    ["Anxiety", "Depression", "Insomnia", "Fatigue", "Loss of Interest", 
     "Difficulty Concentrating", "Changes in Appetite", "Social Withdrawal",
     "Mood Swings", "Physical Discomfort"]
)

# Emergency notice
st.warning("""
⚠️ **Important**: If you're having thoughts of self-harm or experiencing a severe crisis,
please immediately contact emergency services or crisis hotlines:
- National Crisis Hotline: 988
- Emergency: 911
""")

@contextmanager
def agentops_session(api_key: str, tags: list):
    """Context manager for AgentOps sessions"""
    try:
        agentops.init(
            api_key=api_key,
            tags=tags,
            instrument_llm_calls=True,
            auto_start_session=True
        )
        yield
    finally:
        try:
            agentops.end_session("Success")
        except Exception as e:
            print(f"Failed to end AgentOps session: {e}")

# Button to start the agent collaboration
if st.button("Get Support Plan"):
    if not api_key:
        st.error("Please enter your OpenAI API key.")
    else:
        with st.spinner('🤖 AI Agents are analyzing your situation...'):
            with agentops_session(api_key=agentops_key, tags=["mental_health_navigator"]):
                try:
                    task = f"""
                    Create a comprehensive mental health support plan based on:
                    
                    Emotional State: {mental_state}
                    Sleep: {sleep_pattern} hours per night
                    Stress Level: {stress_level}/10
                    Support System: {', '.join(support_system) if support_system else 'None reported'}
                    Recent Changes: {recent_changes}
                    Current Symptoms: {', '.join(current_symptoms) if current_symptoms else 'None reported'}
                    """

                    system_messages = {
                        "psychology_agent": """
                        You are an experienced mental health professional speaking directly to the user. Your task is to:
                        1. Analyze their emotional state and psychological symptoms with empathy
                        2. Help them understand potential mental health concerns
                        3. Assess their risk levels and urgency
                        4. Suggest therapeutic approaches that would work for them
                        5. Help them understand how their life changes and stressors are affecting them
                        6. Provide supportive psychological insights
                        
                        Always use "you" and "your" when addressing the user. Maintain a warm, supportive, and non-judgmental tone.
                        Example: "Based on what you've shared about your sleep patterns..." instead of "The individual's sleep patterns..."
                        """,
                        
                        "resource_agent": """
                        You are a mental health resource coordinator speaking directly to the user. Your task is to:
                        1. Connect you with appropriate mental health services
                        2. Suggest support groups or communities that would benefit you
                        3. Recommend professional care options for your situation
                        4. Provide crisis resources when needed
                        5. Consider what resources would be most accessible for you
                        6. Share specific contact information for your local resources
                        
                        Always address the user directly using "you" and "your". Focus on practical, accessible resources.
                        Example: "Given your current situation, these resources might help..." instead of "The following resources are recommended..."
                        """,
                        
                        "action_agent": """
                        You are a crisis intervention specialist speaking directly to the user. Your task is to:
                        1. Help you develop immediate coping strategies
                        2. Work with you to create a daily wellness routine
                        3. Teach you stress management techniques
                        4. Guide you in improving your sleep habits
                        5. Help you make healthy lifestyle adjustments
                        6. Create an emergency response plan with you if needed
                        
                        Use "you" and "your" when providing guidance. Give clear, actionable steps.
                        Example: "Here are steps you can take right now..." instead of "The following steps are recommended..."
                        """,
                        
                        "followup_agent": """
                        You are a mental health recovery planner speaking directly to the user. Your task is to:
                        1. Help you develop long-term support strategies
                        2. Create a progress monitoring plan that works for you
                        3. Work with you on relapse prevention strategies
                        4. Plan how to engage your support system
                        5. Guide you through lifestyle modifications
                        6. Set up maintenance and check-in schedules with you
                        
                        Always use "you" and "your" in your recommendations. Focus on sustainable, long-term solutions.
                        Example: "To maintain your progress, you might want to..." instead of "The following maintenance plan is suggested..."
                        """
                    }

                    # Then modify the agent configurations
                    llm_config = {
                        "config_list": [{"model": "gpt-4o", "api_key": api_key}]
                    }

                    # Context management for agent communication
                    context_variables = {
                        "psychology": None,
                        "resources": None,
                        "action": None,
                        "followup": None,
                    }

                    # Update functions for each agent
                    def update_psychology_overview(psychology_summary: str, context_variables: dict) -> SwarmResult:
                        """Keep the summary as short as possible."""
                        context_variables["psychology"] = psychology_summary
                        st.sidebar.success('Psychology Analysis: ' + psychology_summary)
                        return SwarmResult(agent="resource_agent", context_variables=context_variables)
                        
                    def update_resource_overview(resource_summary: str, context_variables: dict) -> SwarmResult:
                        """Keep the summary as short as possible."""
                        context_variables["resources"] = resource_summary
                        st.sidebar.success('Resource Identification: ' + resource_summary)
                        return SwarmResult(agent="action_agent", context_variables=context_variables)

                    def update_action_overview(action_summary: str, context_variables: dict) -> SwarmResult:
                        """Keep the summary as short as possible."""
                        context_variables["action"] = action_summary
                        st.sidebar.success('Action Plan: ' + action_summary)
                        return SwarmResult(agent="followup_agent", context_variables=context_variables)

                    def update_followup_overview(followup_summary: str, context_variables: dict) -> SwarmResult:
                        """Keep the summary as short as possible."""
                        context_variables["followup"] = followup_summary
                        st.sidebar.success('Follow-up Strategy: ' + followup_summary)
                        return SwarmResult(agent="psychology_agent", context_variables=context_variables)

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
                    psychology_agent = SwarmAgent(
                        "psychology_agent", 
                        llm_config=llm_config,
                        functions=update_psychology_overview,
                        update_agent_state_before_reply=[state_update]
                    )

                    resource_agent = SwarmAgent(
                        "resource_agent",
                        llm_config=llm_config,
                        functions=update_resource_overview,
                        update_agent_state_before_reply=[state_update]
                    )

                    action_agent = SwarmAgent(
                        "action_agent",
                        llm_config=llm_config,
                        functions=update_action_overview,
                        update_agent_state_before_reply=[state_update]
                    )

                    followup_agent = SwarmAgent(
                        name="followup_agent",
                        llm_config=llm_config,
                        functions=update_followup_overview,
                        update_agent_state_before_reply=[state_update]
                    )

                    psychology_agent.register_hand_off(AFTER_WORK(resource_agent))
                    resource_agent.register_hand_off(AFTER_WORK(action_agent))
                    action_agent.register_hand_off(AFTER_WORK(followup_agent))
                    followup_agent.register_hand_off(AFTER_WORK(psychology_agent))

                    result, _, _ = initiate_swarm_chat(
                        initial_agent=psychology_agent,
                        agents=[psychology_agent, resource_agent, action_agent, followup_agent],
                        user_agent=None,
                        messages=task,
                        max_rounds=13,
                    )

                    # Update session state with the individual responses
                    st.session_state.output = {
                        'psychology': result.chat_history[-4]['content'],
                        'resources': result.chat_history[-3]['content'],
                        'action': result.chat_history[-2]['content'],
                        'followup': result.chat_history[-1]['content']
                    }

                    # Display success message after completion
                    st.success('✨ Mental health support plan generated successfully!')

                    # Display the individual outputs in expanders
                    with st.expander("Psychology Analysis"):
                        st.markdown(st.session_state.output['psychology'])

                    with st.expander("Resource Identification"):
                        st.markdown(st.session_state.output['resources'])

                    with st.expander("Action Plan"):
                        st.markdown(st.session_state.output['action'])

                    with st.expander("Follow-up Strategy"):
                        st.markdown(st.session_state.output['followup'])

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    raise  # Re-raise to trigger session end with error
