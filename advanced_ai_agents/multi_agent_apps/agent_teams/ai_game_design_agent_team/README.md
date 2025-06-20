# AI Game Design Agent Team 🎮

The AI Game Design Agent Team is a collaborative game design system powered by [AG2](https://github.com/ag2ai/ag2?tab=readme-ov-file)(formerly AutoGen)'s AI Agent framework. This app generates comprehensive game concepts through the coordination of multiple specialized AI agents, each focusing on different aspects of game design based on user inputs such as game type, target audience, art style, and technical requirements. This is built on AG2's new swarm feature run through initiate_chat() method.

## Features

- **Specialized Game Design Agent Team**

  - 🎭 **Story Agent**: Specializes in narrative design and world-building, including character development, plot arcs, dialogue writing, and lore creation
  - 🎮 **Gameplay Agent**: Focuses on game mechanics and systems design, including player progression, combat systems, resource management, and balancing
  - 🎨 **Visuals Agent**: Handles art direction and audio design, covering UI/UX, character/environment art style, sound effects, and music composition
  - ⚙️ **Tech Agent**: Provides technical architecture and implementation guidance, including engine selection, optimization strategies, networking requirements, and development roadmap
  - 🎯 **Task Agent**: Coordinates between all specialized agents and ensures cohesive integration of different game aspects

- **Comprehensive Game Design Outputs**:

  - Detailed narrative and world-building elements
  - Core gameplay mechanics and systems
  - Visual and audio direction
  - Technical specifications and requirements
  - Development timeline and budget considerations
  - Coherent game design from the team.

- **Customizable Input Parameters**:

  - Game type and target audience
  - Art style and visual preferences
  - Platform requirements
  - Development constraints (time, budget)
  - Core mechanics and gameplay features

- **Interactive Results**:
  - Quick show of game design ideas from each agent
  - Detailed results are presented in expandable sections for easy navigation and reference

## How to Run

Follow these steps to set up and run the application:

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_game_design_agent_team
   ```

2. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up OpenAI API Key**:

   - Obtain an OpenAI API key from [OpenAI's platform](https://platform.openai.com)
   - You'll input this key in the app's sidebar when running

4. **Run the Streamlit App**:
   ```bash
   streamlit run game_design_agent_team.py
   ```

## Usage

1. Enter your OpenAI API key in the sidebar
2. Fill in the game details:
   - Background vibe and setting
   - Game type and target audience
   - Visual style preferences
   - Technical requirements
   - Development constraints
3. Click "Generate Game Concept" to receive comprehensive design documentation from all agents
4. Review the outputs in the expandable sections for each aspect of game design
