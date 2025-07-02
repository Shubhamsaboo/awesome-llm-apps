# 🎮 Agent X vs Agent O: Tic-Tac-Toe Game

An interactive Tic-Tac-Toe game where two AI agents powered by different language models compete against each other built on Agno Agent Framework and Streamlit as UI.

This example shows how to build an interactive Tic Tac Toe game where AI agents compete against each other. The application showcases how to:
- Coordinate multiple AI agents in a turn-based game
- Use different language models for different players
- Create an interactive web interface with Streamlit
- Handle game state and move validation
- Display real-time game progress and move history

## Features
- Multiple AI models support (GPT-4, Claude, Gemini, etc.)
- Real-time game visualization
- Move history tracking with board states
- Interactive player selection
- Game state management
- Move validation and coordination

## How to Run? 

1. **Setup Environment**
   ```bash
   # Clone the repository
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent

   # Install dependencies
   pip install -r requirements.txt
   ```

### 2. Install dependencies

```shell
pip install -r requirements.txt
```

### 3. Setup API Keys

The game supports multiple AI models. Create a `.env` file in this directory and add your API keys:

1. **Create a `.env` file:**
   ```bash
   # In the ai_tic_tac_toe_agent directory
   touch .env
   ```

2. **Add your API keys to the `.env` file:**
   ```env
   # Required for OpenAI models (gpt-4o, o3-mini)
   OPENAI_API_KEY=your_actual_openai_api_key_here

   # Optional - for additional models
   ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here  # For Claude models
   GOOGLE_API_KEY=your_actual_google_api_key_here        # For Gemini models
   GROQ_API_KEY=your_actual_groq_api_key_here           # For Groq models
   ```

   > **Note:** Replace the placeholder values with your actual API keys. The app will show helpful error messages if required keys are missing.

### 4. Run the Game

```shell
streamlit run app.py
```

- Open [localhost:8501](http://localhost:8501) to view the game interface

## How It Works

The game consists of three agents:

1. **Master Agent (Referee)**
   - Coordinates the game
   - Validates moves
   - Maintains game state
   - Determines game outcome

2. **Two Player Agents**
   - Make strategic moves
   - Analyze board state
   - Follow game rules
   - Respond to opponent moves

## Available Models

The game supports various AI models:
- GPT-4o (OpenAI)
- GPT-o3-mini (OpenAI)
- Gemini (Google)
- Llama 3 (Groq)
- Claude (Anthropic)

## Game Features

1. **Interactive Board**
   - Real-time updates
   - Visual move tracking
   - Clear game status display

2. **Move History**
   - Detailed move tracking
   - Board state visualization
   - Player action timeline

3. **Game Controls**
   - Start/Pause game
   - Reset board
   - Select AI models
   - View game history

4. **Performance Analysis**
   - Move timing
   - Strategy tracking
   - Game statistics
