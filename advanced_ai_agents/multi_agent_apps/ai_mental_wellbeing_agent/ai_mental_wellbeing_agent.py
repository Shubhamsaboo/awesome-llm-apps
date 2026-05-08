import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
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

                assessment_agent = Agent(
                    name="Assessment_Agent",
                    model=OpenAIChat(id="gpt-4o", api_key=api_key),
                    description="Analyzes emotional state and mental health needs",
                    instructions=[
                        "You are an experienced mental health professional speaking directly to the user.",
                        "Create a safe space by acknowledging their courage in seeking support",
                        "Analyze their emotional state with clinical precision and genuine empathy",
                        "Ask targeted follow-up questions to understand their full situation",
                        "Identify patterns in their thoughts, behaviors, and relationships",
                        "Assess risk levels with validated screening approaches",
                        "Help them understand their current mental health in accessible language",
                        "Validate their experiences without minimizing or catastrophizing"
                    ],
                    tools=[DuckDuckGoTools()]
                )

                action_agent = Agent(
                    name="Action_Agent",
                    model=OpenAIChat(id="gpt-4o", api_key=api_key),
                    description="Creates immediate action plan and connects with resources",
                    instructions=[
                        "You are a crisis intervention and resource specialist speaking directly to the user.",
                        "Provide immediate evidence-based coping strategies tailored to their specific situation",
                        "Prioritize interventions based on urgency and effectiveness",
                        "Connect them with appropriate mental health services while acknowledging barriers",
                        "Create a concrete daily wellness plan with specific times and activities",
                        "Suggest specific support communities with details on how to join",
                        "Balance crisis resources with empowerment techniques",
                        "Teach simple self-regulation techniques they can use immediately"
                    ],
                    tools=[DuckDuckGoTools()]
                )

                followup_agent = Agent(
                    name="Followup_Agent",
                    model=OpenAIChat(id="gpt-4o", api_key=api_key),
                    description="Designs long-term support strategy",
                    instructions=[
                        "You are a mental health recovery planner speaking directly to the user.",
                        "Design a personalized long-term support strategy with milestone markers",
                        "Create a progress monitoring system that matches their preferences and habits",
                        "Develop specific relapse prevention strategies based on their unique triggers",
                        "Establish a support network mapping exercise to identify existing resources",
                        "Build a graduated self-care routine that evolves with their recovery",
                        "Plan for setbacks with self-compassion techniques",
                        "Set up a maintenance schedule with clear check-in mechanisms"
                    ],
                    tools=[DuckDuckGoTools()]
                )

                with st.container():
                    st.subheader("🎭 Assessment")
                    assessment_response = assessment_agent.run(task)
                    st.markdown(assessment_response.content)
                    st.session_state.output['assessment'] = assessment_response.content

                with st.container():
                    st.subheader("🎯 Action Plan")
                    action_task = f"Based on this assessment: {assessment_response.content}\n\nCreate an action plan."
                    action_response = action_agent.run(action_task)
                    st.markdown(action_response.content)
                    st.session_state.output['action'] = action_response.content

                with st.container():
                    st.subheader("🔄 Long-term Strategy")
                    followup_task = f"Based on assessment: {assessment_response.content}\n\nAnd action plan: {action_response.content}\n\nCreate a follow-up strategy."
                    followup_response = followup_agent.run(followup_task)
                    st.markdown(followup_response.content)
                    st.session_state.output['followup'] = followup_response.content

                st.success('✨ Mental health support plan generated successfully!')

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
