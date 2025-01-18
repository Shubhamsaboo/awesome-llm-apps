import streamlit as st
import autogen
from autogen.agentchat import GroupChat, GroupChatManager

# Initialize session state
if 'output' not in st.session_state:
    st.session_state.output = {'story': '', 'gameplay': '', 'visuals': '', 'tech': ''}

# Sidebar for API key input
st.sidebar.title("API Key")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")

# Add guidance in sidebar
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

# Main app UI
st.title("🎮 AI Game Design Agent Team")

# Add agent information below title
st.info("""
**Meet Your AI Game Design Team:**

🎭 **Story Agent** - Crafts compelling narratives and rich worlds

🎮 **Gameplay Agent** - Creates engaging mechanics and systems

🎨 **Visuals Agent** - Shapes the artistic vision and style

⚙️ **Tech Agent** - Provides technical direction and solutions
                
These agents collaborate to create a comprehensive game concept based on your inputs.
""")

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
        with st.spinner('🤖 AI Agents are collaborating on your game concept...'):
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
            llm_config = {
                "timeout": 600,
                "cache_seed": 44,  # change the seed for different trials
                "config_list": [
                    {
                        "model": "gpt-4o-mini",
                        "api_key": api_key,
                    }
                ],
                "temperature": 0,
            }

            # Define a task-provider agent
            task_agent = autogen.AssistantAgent(
                name="task_agent",
                llm_config=llm_config,
                system_message="You are a task provider. Your only job is to provide the task details to the other agents.",
            )

            # Define agents with detailed system prompts
            story_agent = autogen.AssistantAgent(
                name="story_agent",
                llm_config=llm_config,
                system_message="""
                You are an experienced game story designer specializing in narrative design and world-building. Your task is to:
                1. Create a compelling narrative that aligns with the specified game type and target audience.
                2. Design memorable characters with clear motivations and character arcs.
                3. Develop the game's world, including its history, culture, and key locations.
                4. Plan story progression and major plot points.
                5. Integrate the narrative with the specified mood/atmosphere.
                6. Consider how the story supports the core gameplay mechanics.
                Provide your response in a detailed, well-structured report format. Do not use XML tags.
                """
            )

            gameplay_agent = autogen.AssistantAgent(
                name="gameplay_agent",
                llm_config=llm_config,
                system_message="""
                You are a senior game mechanics designer with expertise in player engagement and systems design. Your task is to:
                1. Design core gameplay loops that match the specified game type and mechanics.
                2. Create progression systems (character development, skills, abilities).
                3. Define player interactions and control schemes for the chosen perspective.
                4. Balance gameplay elements for the target audience.
                5. Design multiplayer interactions if applicable.
                6. Specify game modes and difficulty settings.
                7. Consider the budget and development time constraints.
                Provide your response in a detailed, well-structured report format. Do not use XML tags.
                """
            )

            visuals_agent = autogen.AssistantAgent(
                name="visuals_agent",
                llm_config=llm_config,
                system_message="""
                You are a creative art director with expertise in game visual and audio design. Your task is to:
                1. Define the visual style guide matching the specified art style.
                2. Design character and environment aesthetics.
                3. Plan visual effects and animations.
                4. Create the audio direction including music style, sound effects, and ambient sound.
                5. Consider technical constraints of chosen platforms.
                6. Align visual elements with the game's mood/atmosphere.
                7. Work within the specified budget constraints.
                Provide your response in a detailed, well-structured report format. Do not use XML tags.
                """
            )

            tech_agent = autogen.AssistantAgent(
                name="tech_agent",
                llm_config=llm_config,
                system_message="""
                You are a technical director with extensive game development experience. Your task is to:
                1. Recommend appropriate game engine and development tools.
                2. Define technical requirements for all target platforms.
                3. Plan the development pipeline and asset workflow.
                4. Identify potential technical challenges and solutions.
                5. Estimate resource requirements within the budget.
                6. Consider scalability and performance optimization.
                7. Plan for multiplayer infrastructure if applicable.
                Provide your response in a detailed, well-structured report format. Do not use XML tags.
                """
            )

            # Function to run agents sequentially
            def run_agents_sequentially(task):
                # Task agent provides the task to each agent one by one
                task_agent.initiate_chat(story_agent, message=task, max_turns=1)
                story_response = story_agent.last_message()["content"]

                task_agent.initiate_chat(gameplay_agent, message=task, max_turns=1)
                gameplay_response = gameplay_agent.last_message()["content"]

                task_agent.initiate_chat(visuals_agent, message=task, max_turns=1)
                visuals_response = visuals_agent.last_message()["content"]

                task_agent.initiate_chat(tech_agent, message=task, max_turns=1)
                tech_response = tech_agent.last_message()["content"]

                return {
                    "story": story_response,
                    "gameplay": gameplay_response,
                    "visuals": visuals_response,
                    "tech": tech_response,
                }

            # Run the agents sequentially and capture their responses
            individual_responses = run_agents_sequentially(task)

            # Update session state with the individual responses
            st.session_state.output = individual_responses

        # Display success message after completion
        st.success('✨ Game concept generated successfully!')

        # Display the individual outputs in expanders
        with st.expander("Story Design"):
            st.markdown(st.session_state.output['story'])

        with st.expander("Gameplay Mechanics"):
            st.markdown(st.session_state.output['gameplay'])

        with st.expander("Visual and Audio Design"):
            st.markdown(st.session_state.output['visuals'])

        with st.expander("Technical Recommendations"):
            st.markdown(st.session_state.output['tech'])

        groupchat = GroupChat(
            agents=[task_agent, story_agent, gameplay_agent, visuals_agent, tech_agent],
            messages=[],
            speaker_selection_method="round_robin",  # Ensures agents speak in order
            allow_repeat_speaker=False,  # Prevents agents from speaking more than once
            max_round=5,  # Each agent speaks exactly once
        )

        # Create the group chat manager
        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config=llm_config,
            is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
        )

        # Function to run the agent collaboration
        def run_agents(task):
            task_agent.initiate_chat(manager, message=task)
            return {
                "story": story_agent.last_message()["content"],
                "gameplay": gameplay_agent.last_message()["content"],
                "visuals": visuals_agent.last_message()["content"],
                "tech": tech_agent.last_message()["content"],
            }
