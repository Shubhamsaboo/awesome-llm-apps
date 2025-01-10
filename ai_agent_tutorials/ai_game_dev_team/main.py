import streamlit as st
import asyncio
from autogen import AssistantAgent
from autogen.agentchat.groupchat import RoundRobinGroupChat
from autogen.agentchat.conditions import TextMentionTermination
from autogen.oai.client import OpenAIWrapper

# Initialize session state
if 'output' not in st.session_state:
    st.session_state.output = {'story': '', 'gameplay': '', 'visuals': '', 'tech': ''}

# Sidebar for API key input
st.sidebar.title("API Key")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")

# Main app UI
st.title("Game Development AI Agent Collaboration")

# User inputs
st.subheader("Game Details")
col1, col2 = st.columns(2)

with col1:
    background_vibe = st.text_input("Background Vibe", "Epic fantasy with dragons")
    game_type = st.selectbox("Game Type", ["RPG", "Action", "Adventure", "Puzzle", "Strategy", "Simulation", "Platform", "Horror"])
    target_audience = st.selectbox("Target Audience", ["Kids (7-12)", "Teens (13-17)", "Young Adults (18-25)", "Adults (26+)", "All Ages"])
    player_perspective = st.selectbox("Player Perspective", ["First Person", "Third Person", "Top Down", "Side View", "Isometric"])
    multiplayer = st.selectbox("Multiplayer Support", ["Single Player Only", "Local Co-op", "Online Multiplayer", "Both Local and Online"])

with col2:
    game_goal = st.text_input("Game Goal", "Save the kingdom from eternal winter")
    art_style = st.selectbox("Art Style", ["Realistic", "Cartoon", "Pixel Art", "Stylized", "Low Poly", "Anime", "Hand-drawn"])
    platform = st.multiselect("Target Platforms", ["PC", "Mobile", "PlayStation", "Xbox", "Nintendo Switch", "Web Browser"])
    development_time = st.slider("Development Time (months)", 1, 36, 12)
    cost = st.number_input("Budget (USD)", min_value=0, value=10000, step=5000)

# Additional details
st.subheader("Detailed Preferences")
col3, col4 = st.columns(2)

with col3:
    core_mechanics = st.multiselect(
        "Core Gameplay Mechanics",
        ["Combat", "Exploration", "Puzzle Solving", "Resource Management", "Base Building", "Stealth", "Racing", "Crafting"]
    )
    mood = st.multiselect(
        "Game Mood/Atmosphere",
        ["Epic", "Mysterious", "Peaceful", "Tense", "Humorous", "Dark", "Whimsical", "Scary"]
    )

with col4:
    inspiration = st.text_area("Games for Inspiration (comma-separated)", "")
    unique_features = st.text_area("Unique Features or Requirements", "")

depth = st.selectbox("Level of Detail in Response", ["Low", "Medium", "High"])

# Button to start the agent collaboration
if st.button("Generate Game Concept"):
    # Check if API key is provided
    if not api_key:
        st.error("Please enter your OpenAI API key.")
    else:
        # Prepare the task based on user inputs
        task = f"""
        Create a game concept with the following details:
        - Background Vibe: {background_vibe}
        - Game Type: {game_type}
        - Game Goal: {game_goal}
        - Target Audience: {target_audience}
        - Player Perspective: {player_perspective}
        - Multiplayer Support: {multiplayer}
        - Art Style: {art_style}
        - Target Platforms: {', '.join(platform)}
        - Development Time: {development_time} months
        - Budget: ${cost:,}
        - Core Mechanics: {', '.join(core_mechanics)}
        - Mood/Atmosphere: {', '.join(mood)}
        - Inspiration: {inspiration}
        - Unique Features: {unique_features}
        - Detail Level: {depth}
        """

        # Configure OpenAI model client with the API key
        model_client = OpenAIWrapper(
            model="gpt-4-0613",
            api_key=api_key
        )

        # Define agents with detailed system prompts
        story_agent = AssistantAgent(
            "story_agent",
            model_client=model_client,
            system_message="""
            You are a game story designer. Your task is to create a compelling narrative for the game.
            Include details about the world, characters, and plot. Make the story immersive and engaging.
            """
        )

        gameplay_agent = AssistantAgent(
            "gameplay_agent",
            model_client=model_client,
            system_message="""
            You are a game mechanics designer. Your task is to define the core gameplay mechanics, features, and systems.
            Include details about combat, exploration, progression, and unique features.
            """
        )

        visuals_agent = AssistantAgent(
            "visuals_agent",
            model_client=model_client,
            system_message="""
            You are a visual and audio designer. Your task is to define the art style, environment design, and audio elements.
            Include details about the color palette, character design, and sound effects.
            """
        )

        tech_agent = AssistantAgent(
            "tech_agent",
            model_client=model_client,
            system_message="""
            You are a technical expert. Your task is to recommend the technology stack, tools, and implementation plan.
            Include details about the game engine, programming languages, and tools for asset creation.
            """
        )

        # Define termination condition
        text_termination = TextMentionTermination("APPROVE")

        # Create the team
        team = RoundRobinGroupChat(
            [story_agent, gameplay_agent, visuals_agent, tech_agent],
            termination_condition=text_termination
        )

        # Function to run the agent collaboration
        async def run_agents(task):
            result = await team.run(task=task)
            return result.content

        # Run the agents and get the result
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_agents(task))

        # Parse the result and update session state
        st.session_state.output['story'] = result.split("Story:")[1].split("Gameplay:")[0].strip()
        st.session_state.output['gameplay'] = result.split("Gameplay:")[1].split("Visuals:")[0].strip()
        st.session_state.output['visuals'] = result.split("Visuals:")[1].split("Tech:")[0].strip()
        st.session_state.output['tech'] = result.split("Tech:")[1].strip()

        # Display the outputs in containers
        with st.container():
            st.subheader("Story")
            st.write(st.session_state.output['story'])

        with st.container():
            st.subheader("Gameplay Mechanics")
            st.write(st.session_state.output['gameplay'])

        with st.container():
            st.subheader("Visual and Audio Design")
            st.write(st.session_state.output['visuals'])

        with st.container():
            st.subheader("Technical Recommendations")
            st.write(st.session_state.output['tech'])