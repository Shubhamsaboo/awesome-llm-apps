import streamlit as st
import asyncio
import autogen
from autogen.agentchat import GroupChat, GroupChatManager
from bs4 import BeautifulSoup

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
        llm_config = {
            "timeout": 600,
            "cache_seed": 44,  # change the seed for different trials
            "config_list": [
                {
                    "model": "gpt-4",
                    "api_key": api_key,
                }
            ],
            "temperature": 0,
        }

        # Define agents with detailed system prompts
        story_agent = autogen.AssistantAgent(
            name="story_agent",
            llm_config=llm_config,
            system_message="""
            You are an experienced game story designer specializing in narrative design and world-building. Your task is to:
            1. Create a compelling narrative that aligns with the specified game type and target audience
            2. Design memorable characters with clear motivations and character arcs
            3. Develop the game's world, including its history, culture, and key locations
            4. Plan story progression and major plot points
            5. Integrate the narrative with the specified mood/atmosphere
            6. Consider how the story supports the core gameplay mechanics
            
            Structure your response using these XML tags:
            <story>
                <world_overview>
                    [Describe the game world, its history, and setting]
                </world_overview>
                <main_characters>
                    <character>
                        <name>[Character name]</name>
                        <role>[Character role]</role>
                        <motivation>[Character motivation]</motivation>
                        <arc>[Character development arc]</arc>
                    </character>
                </main_characters>
                <plot_structure>
                    <beginning>[Opening act]</beginning>
                    <middle>[Main story development]</middle>
                    <climax>[Story climax]</climax>
                    <resolution>[Story resolution]</resolution>
                </plot_structure>
                <key_moments>[List of pivotal story moments]</key_moments>
                <gameplay_integration>[How story elements connect with gameplay]</gameplay_integration>
            </story>
            """
        )

        gameplay_agent = autogen.AssistantAgent(
            name="gameplay_agent",
            llm_config=llm_config,
            system_message="""
            You are a senior game mechanics designer with expertise in player engagement and systems design. Your task is to:
            1. Design core gameplay loops that match the specified game type and mechanics
            2. Create progression systems (character development, skills, abilities)
            3. Define player interactions and control schemes for the chosen perspective
            4. Balance gameplay elements for the target audience
            5. Design multiplayer interactions if applicable
            6. Specify game modes and difficulty settings
            7. Consider the budget and development time constraints
            
            Structure your response using these XML tags:
            <gameplay>
                <core_loop>
                    <primary_loop>[Main gameplay loop]</primary_loop>
                    <secondary_loops>[Supporting gameplay loops]</secondary_loops>
                </core_loop>
                <controls>
                    <input_scheme>[Control scheme details]</input_scheme>
                    <player_actions>[List of player actions]</player_actions>
                </controls>
                <progression>
                    <character_development>[Skills, abilities, stats]</character_development>
                    <unlockables>[Items, features, content]</unlockables>
                    <achievements>[Key milestones and rewards]</achievements>
                </progression>
                <game_modes>[List and description of game modes]</game_modes>
                <multiplayer_features>[Multiplayer mechanics if applicable]</multiplayer_features>
                <balance>[Game balance considerations]</balance>
            </gameplay>
            """
        )

        visuals_agent = autogen.AssistantAgent(
            name="visuals_agent",
            llm_config=llm_config,
            system_message="""
            You are a creative art director with expertise in game visual and audio design. Your task is to:
            1. Define the visual style guide matching the specified art style
            2. Design character and environment aesthetics
            3. Plan visual effects and animations
            4. Create the audio direction including music style, sound effects, and ambient sound
            5. Consider technical constraints of chosen platforms
            6. Align visual elements with the game's mood/atmosphere
            7. Work within the specified budget constraints
            
            Structure your response using these XML tags:
            <visuals>
                <style_guide>
                    <color_palette>[Color scheme details]</color_palette>
                    <art_direction>[Overall visual direction]</art_direction>
                    <reference_materials>[Visual references]</reference_materials>
                </style_guide>
                <character_design>
                    <main_characters>[Main character visual details]</main_characters>
                    <npc_guidelines>[NPC design guidelines]</npc_guidelines>
                </character_design>
                <environment>
                    <world_aesthetics>[World design principles]</world_aesthetics>
                    <key_locations>[Notable location designs]</key_locations>
                </environment>
                <vfx_animation>
                    <effects_style>[VFX guidelines]</effects_style>
                    <animation_principles>[Animation guidelines]</animation_principles>
                </vfx_animation>
                <audio>
                    <music>[Music style and themes]</music>
                    <sound_effects>[SFX guidelines]</sound_effects>
                    <ambient>[Environmental audio]</ambient>
                </audio>
                <technical_specs>[Platform-specific considerations]</technical_specs>
            </visuals>
            """
        )

        tech_agent = autogen.AssistantAgent(
            name="tech_agent",
            llm_config=llm_config,
            system_message="""
            You are a technical director with extensive game development experience. Your task is to:
            1. Recommend appropriate game engine and development tools
            2. Define technical requirements for all target platforms
            3. Plan the development pipeline and asset workflow
            4. Identify potential technical challenges and solutions
            5. Estimate resource requirements within the budget
            6. Consider scalability and performance optimization
            7. Plan for multiplayer infrastructure if applicable
            
            Structure your response using these XML tags:
            <technical>
                <stack>
                    <engine>[Game engine choice and rationale]</engine>
                    <tools>[Development tools list]</tools>
                    <languages>[Programming languages]</languages>
                </stack>
                <pipeline>
                    <asset_workflow>[Asset creation and management]</asset_workflow>
                    <build_process>[Build and deployment process]</build_process>
                    <version_control>[Version control strategy]</version_control>
                </pipeline>
                <requirements>
                    <platforms>[Platform-specific requirements]</platforms>
                    <performance>[Performance targets]</performance>
                    <networking>[Network requirements if applicable]</networking>
                </requirements>
                <resources>
                    <team>[Team composition and roles]</team>
                    <hardware>[Hardware requirements]</hardware>
                    <hosting>[Server infrastructure if needed]</hosting>
                </resources>
                <timeline>
                    <phases>[Development phases]</phases>
                    <milestones>[Key technical milestones]</milestones>
                    <risks>[Technical risks and mitigation]</risks>
                </timeline>
            </technical>
            """
        )

        # Create the group chat
        groupchat = GroupChat(
            agents=[story_agent, gameplay_agent, visuals_agent, tech_agent],
            messages=[],
            speaker_selection_method="round_robin",
            allow_repeat_speaker=False,
            max_round=12,
        )

        # Create the group chat manager
        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config=llm_config,
            is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
        )

        # Function to run the agent collaboration
        async def run_agents(task):
            await story_agent.initiate_chat(manager, message=task)
            return manager.last_message()["content"]

        # Run the agents and get the result
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_agents(task))

        # Parse the result and update session state
        soup = BeautifulSoup(result, 'xml')

        # Extract sections
        st.session_state.output['story'] = str(soup.find('story'))
        st.session_state.output['gameplay'] = str(soup.find('gameplay'))
        st.session_state.output['visuals'] = str(soup.find('visuals'))
        st.session_state.output['tech'] = str(soup.find('technical'))

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