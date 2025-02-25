# Agent Tic Tac Toe

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

### 1. Create a virtual environment

```shell
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```shell
pip install -r ai_agent_tutorials/ai_tic_tac_toe_game/requirements.txt
```

### 3. Export API Keys

The game supports multiple AI models. Export the API keys for the models you want to use:

```shell
# Required for OpenAI models
export OPENAI_API_KEY=***

# Optional - for additional models
export ANTHROPIC_API_KEY=***  # For Claude models
export GOOGLE_API_KEY=***     # For Gemini models
export GROQ_API_KEY=***       # For Groq models
```

### 4. Run the Game

```shell
streamlit run ai_agent_tutorials/ai_tic_tac_toe_game/app.py
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

## Support

Join our [Discord community](https://agno.link/discord) for help and discussions.
