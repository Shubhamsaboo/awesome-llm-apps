import streamlit as st
from autogen import (SwarmAgent, SwarmResult, initiate_swarm_chat, OpenAIWrapper,AFTER_WORK,UPDATE_SYSTEM_MESSAGE)
import os

os.environ["AUTOGEN_USE_DOCKER"] = "0"

if 'output' not in st.session_state:
    st.session_state.output = {
        'assessment': '',
        'action': '',
        'followup': ''
    }

st.sidebar.title("OpenAI API Key")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")

st.sidebar.warning("""
## ⚠️ Important Notice

This application is a supportive tool and does not replace professional mental health care. If you're experiencing thoughts of self-harm or severe crisis:

- Call National Crisis Hotline: 988
- Call Emergency Services: 911
- Seek immediate professional help
""")

st.title("🧠 Mental Wellbeing Agent")

st.info("""
**Meet Your Mental Wellbeing Agent Team:**

🧠 **Assessment Agent** - Analyzes your situation and emotional needs
🎯 **Action Agent** - Creates immediate action plan and connects you with resources
🔄 **Follow-up Agent** - Designs your long-term support strategy
""")

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

if st.button("Get Support Plan"):
    if not api_key:
        st.error("Please enter your OpenAI API key.")
    else:
        with st.spinner('🤖 AI Agents are analyzing your situation...'):
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
                    "assessment_agent": """
                    You are an experienced mental health professional speaking directly to the user. Your task is to:
                    1. Create a safe space by acknowledging their courage in seeking support
                    2. Analyze their emotional state with clinical precision and genuine empathy
                    3. Ask targeted follow-up questions to understand their full situation
                    4. Identify patterns in their thoughts, behaviors, and relationships
                    5. Assess risk levels with validated screening approaches
                    6. Help them understand their current mental health in accessible language
                    7. Validate their experiences without minimizing or catastrophizing

                    Always use "you" and "your" when addressing the user. Blend clinical expertise with genuine warmth and never rush to conclusions.
                    """,
                    
                    "action_agent": """
                    You are a crisis intervention and resource specialist speaking directly to the user. Your task is to:
                    1. Provide immediate evidence-based coping strategies tailored to their specific situation
                    2. Prioritize interventions based on urgency and effectiveness
                    3. Connect them with appropriate mental health services while acknowledging barriers (cost, access, stigma)
                    4. Create a concrete daily wellness plan with specific times and activities
                    5. Suggest specific support communities with details on how to join
                    6. Balance crisis resources with empowerment techniques
                    7. Teach simple self-regulation techniques they can use immediately

                    Focus on practical, achievable steps that respect their current capacity and energy levels. Provide options ranging from minimal effort to more involved actions.
                    """,
                    
                    "followup_agent": """
                    You are a mental health recovery planner speaking directly to the user. Your task is to:
                    1. Design a personalized long-term support strategy with milestone markers
                    2. Create a progress monitoring system that matches their preferences and habits
                    3. Develop specific relapse prevention strategies based on their unique triggers
                    4. Establish a support network mapping exercise to identify existing resources
                    5. Build a graduated self-care routine that evolves with their recovery
                    6. Plan for setbacks with self-compassion techniques
                    7. Set up a maintenance schedule with clear check-in mechanisms

                    Focus on building sustainable habits that integrate with their lifestyle and values. Emphasize progress over perfection and teach skills for self-directed care.
                    """
                }

                llm_config = {
                    "config_list": [{"model": "gpt-4o", "api_key": api_key}]
                }

                context_variables = {
                    "assessment": None,
                    "action": None,
                    "followup": None,
                }

                def update_assessment_overview(assessment_summary: str, context_variables: dict) -> SwarmResult:
                    context_variables["assessment"] = assessment_summary
                    st.sidebar.success('Assessment: ' + assessment_summary)
                    return SwarmResult(agent="action_agent", context_variables=context_variables)

                def update_action_overview(action_summary: str, context_variables: dict) -> SwarmResult:
                    context_variables["action"] = action_summary
                    st.sidebar.success('Action Plan: ' + action_summary)
                    return SwarmResult(agent="followup_agent", context_variables=context_variables)

                def update_followup_overview(followup_summary: str, context_variables: dict) -> SwarmResult:
                    context_variables["followup"] = followup_summary
                    st.sidebar.success('Follow-up Strategy: ' + followup_summary)
                    return SwarmResult(agent="assessment_agent", context_variables=context_variables)

                def update_system_message_func(agent: SwarmAgent, messages) -> str:
                    system_prompt = system_messages[agent.name]
                    current_gen = agent.name.split("_")[0]
                    
                    if agent._context_variables.get(current_gen) is None:
                        system_prompt += f"Call the update function provided to first provide a 2-3 sentence summary of your ideas on {current_gen.upper()} based on the context provided."
                        agent.llm_config['tool_choice'] = {"type": "function", "function": {"name": f"update_{current_gen}_overview"}}
                    else:
                        agent.llm_config["tools"] = None
                        agent.llm_config['tool_choice'] = None
                        system_prompt += f"\n\nYour task\nYou task is write the {current_gen} part of the report. Do not include any other parts. Do not use XML tags.\nStart your reponse with: '## {current_gen.capitalize()} Design'."    
                        k = list(agent._oai_messages.keys())[-1]
                        agent._oai_messages[k] = agent._oai_messages[k][:1]

                    system_prompt += f"\n\n\nBelow are some context for you to refer to:"
                    for k, v in agent._context_variables.items():
                        if v is not None:
                            system_prompt += f"\n{k.capitalize()} Summary:\n{v}"

                    agent.client = OpenAIWrapper(**agent.llm_config)
                    return system_prompt
                
                state_update = UPDATE_SYSTEM_MESSAGE(update_system_message_func)

                assessment_agent = SwarmAgent(
                    "assessment_agent", 
                    llm_config=llm_config,
                    functions=update_assessment_overview,
                    update_agent_state_before_reply=[state_update]
                )

                action_agent = SwarmAgent(
                    "action_agent",
                    llm_config=llm_config,
                    functions=update_action_overview,
                    update_agent_state_before_reply=[state_update]
                )

                followup_agent = SwarmAgent(
                    "followup_agent",
                    llm_config=llm_config,
                    functions=update_followup_overview,
                    update_agent_state_before_reply=[state_update]
                )

                assessment_agent.register_hand_off(AFTER_WORK(action_agent))
                action_agent.register_hand_off(AFTER_WORK(followup_agent))
                followup_agent.register_hand_off(AFTER_WORK(assessment_agent))

                result, _, _ = initiate_swarm_chat(
                    initial_agent=assessment_agent,
                    agents=[assessment_agent, action_agent, followup_agent],
                    user_agent=None,
                    messages=task,
                    max_rounds=13,
                )

                st.session_state.output = {
                    'assessment': result.chat_history[-3]['content'],
                    'action': result.chat_history[-2]['content'],
                    'followup': result.chat_history[-1]['content']
                }

                with st.expander("Situation Assessment"):
                    st.markdown(st.session_state.output['assessment'])

                with st.expander("Action Plan & Resources"):
                    st.markdown(st.session_state.output['action'])

                with st.expander("Long-term Support Strategy"):
                    st.markdown(st.session_state.output['followup'])

                st.success('✨ Mental health support plan generated successfully!')

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
