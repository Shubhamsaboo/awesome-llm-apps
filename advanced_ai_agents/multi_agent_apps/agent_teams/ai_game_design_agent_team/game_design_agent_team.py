import asyncio
import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

if 'output' not in st.session_state:
    st.session_state.output = {'story': '', 'gameplay': '', 'visuals': '', 'tech': ''}

st.sidebar.title("API Key")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")

st.sidebar.success("""
✨ **Getting Started**

Please provide inputs and features for your dream game! Consider:
- The overall vibe and setting
- Core gameplay elements
- Target audience and platforms
- Visual style preferences
- Technical requirements

The AI agents will collaborate to develop a comprehensive game concept based on your specifications.
""")

st.title("🎮 AI Game Design Agent Team")

st.info("""
**Meet Your AI Game Design Team:**

🎭 **Story Agent** - Crafts compelling narratives and rich worlds
🎮 **Gameplay Agent** - Creates engaging mechanics and systems
🎨 **Visuals Agent** - Shapes the artistic vision and style
⚙️ **Tech Agent** - Provides technical direction and solutions

These agents collaborate to create a comprehensive game concept based on your inputs.
""")

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

if st.button("Generate Game Concept"):
    if not api_key:
        st.error("Please enter your OpenAI API key.")
    else:
        with st.spinner('🤖 AI Agents are collaborating on your game concept...'):
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

            story_agent = Agent(
                name="Story_Agent",
                model=OpenAIChat(id="gpt-4o-mini", api_key=api_key),
                description="Crafts compelling narratives and rich worlds",
                instructions=[
                    "You are an experienced game story designer specializing in narrative design and world-building.",
                    "Create a compelling narrative that aligns with the specified game type and target audience.",
                    "Design memorable characters with clear motivations and character arcs.",
                    "Develop the game's world, including its history, culture, and key locations.",
                    "Plan story progression and major plot points.",
                    "Integrate the narrative with the specified mood/atmosphere.",
                    "Consider how the story supports the core gameplay mechanics."
                ],
                tools=[DuckDuckGoTools()]
            )

            gameplay_agent = Agent(
                name="Gameplay_Agent",
                model=OpenAIChat(id="gpt-4o-mini", api_key=api_key),
                description="Creates engaging mechanics and systems",
                instructions=[
                    "You are a senior game mechanics designer with expertise in player engagement and systems design.",
                    "Design core gameplay loops that match the specified game type and mechanics.",
                    "Create progression systems (character development, skills, abilities).",
                    "Define player interactions and control schemes for the chosen perspective.",
                    "Balance gameplay elements for the target audience.",
                    "Design multiplayer interactions if applicable.",
                    "Specify game modes and difficulty settings.",
                    "Consider the budget and development time constraints."
                ],
                tools=[DuckDuckGoTools()]
            )

            visuals_agent = Agent(
                name="Visuals_Agent",
                model=OpenAIChat(id="gpt-4o-mini", api_key=api_key),
                description="Shapes the artistic vision and style",
                instructions=[
                    "You are a creative art director with expertise in game visual and audio design.",
                    "Define the visual style guide matching the specified art style.",
                    "Design character and environment aesthetics.",
                    "Plan visual effects and animations.",
                    "Create the audio direction including music style, sound effects, and ambient sound.",
                    "Consider technical constraints of chosen platforms.",
                    "Align visual elements with the game's mood/atmosphere.",
                    "Work within the specified budget constraints."
                ],
                tools=[DuckDuckGoTools()]
            )

            tech_agent = Agent(
                name="Tech_Agent",
                model=OpenAIChat(id="gpt-4o-mini", api_key=api_key),
                description="Provides technical direction and solutions",
                instructions=[
                    "You are a technical director with extensive game development experience.",
                    "Recommend appropriate game engine and development tools.",
                    "Define technical requirements for all target platforms.",
                    "Plan the development pipeline and asset workflow.",
                    "Identify potential technical challenges and solutions.",
                    "Estimate resource requirements within the budget.",
                    "Consider scalability and performance optimization.",
                    "Plan for multiplayer infrastructure if applicable."
                ],
                tools=[DuckDuckGoTools()]
            )

            with st.container():
                st.subheader("🎭 Story Design")
                story_response = story_agent.run(task)
                st.markdown(story_response.content)
                st.session_state.output['story'] = story_response.content

            with st.container():
                st.subheader("🎮 Gameplay Mechanics")
                gameplay_task = f"Building on the story: {story_response.content}\n\nDesign gameplay mechanics."
                gameplay_response = gameplay_agent.run(gameplay_task)
                st.markdown(gameplay_response.content)
                st.session_state.output['gameplay'] = gameplay_response.content

            with st.container():
                st.subheader("🎨 Visual and Audio Design")
                visuals_task = f"Story: {story_response.content}\nGameplay: {gameplay_response.content}\n\nDesign visuals and audio."
                visuals_response = visuals_agent.run(visuals_task)
                st.markdown(visuals_response.content)
                st.session_state.output['visuals'] = visuals_response.content

            with st.container():
                st.subheader("⚙️ Technical Recommendations")
                tech_task = f"Story: {story_response.content}\nGameplay: {gameplay_response.content}\nVisuals: {visuals_response.content}\n\nProvide technical recommendations."
                tech_response = tech_agent.run(tech_task)
                st.markdown(tech_response.content)
                st.session_state.output['tech'] = tech_response.content

            st.success('✨ Game concept generated successfully!')
