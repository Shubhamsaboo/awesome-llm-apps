# 🎮 Agent X vs Agent O: Tic-Tac-Toe Game

An interactive Tic-Tac-Toe game where two AI agents powered by different language models compete against each other built on Agno Agent Framework and Streamlit as UI. Watch as GPT-4O battles against either DeepSeek V3 or Google's Gemini 1.5 Flash in this classic game.

## Features

### Multi-Agent System
- Player X: OpenAI's Gemini Flash 2.0
- Player O: DeepSeek v3
- Judge: GPT-4o for game outcome validation

### Interactive Interface
- Real-time game board visualization
- Move-by-move analysis
- Agent response tracking
- Clear game status updates

### Strategic Gameplay
- AI-powered move decisions
- Winning strategy implementation
- Opponent move blocking
- Victory condition monitoring

## Prerequisites 
- Python 3.8+
- OpenAI API key
- Either DeepSeek API key or Google API key (for Player O)

## How to Run 

1. **Setup Environment**
   ```bash
   # Clone the repository
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd ai_agent_tutorials/ai_tic_tac_toe_agent

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   - Get OpenAI API key from [OpenAI Platform](https://platform.openai.com)
   - Get Google API key from [Google AI Studio](https://aistudio.google.com) (if using Gemini)
   - Get DeepSeek API key from DeepSeek platform [Deepseek platform](https://www.deepseek.com) (if using DeepSeek v3 model)

4. **Run the Application**
   ```bash
   streamlit run ai_tic_tac_toe_agent.py
   ```

5. **Using the Interface**
   - Enter your API keys in the sidebar
   - Click "Start Game" to begin
   - Watch as the AI agents battle it out!
   - Monitor the game progress and final results

## Game Components

- **Game Board**
  - 3x3 interactive grid
  - Real-time move visualization
  - Clear symbol placement (X/O)

- **AI Agent Players**
  - Player X: Strategic offensive moves
  - Player O: Defensive countermoves since this agent started later
  - AI Judge: Game outcome validation

- **Game Flow**
  - Alternating turns between AIs
  - Move validation and error handling
  - Winner determination
  - Draw detection

## Disclaimer ⚠️

This is a demonstration project showcasing AI capabilities in game playing. API costs will apply based on your usage of the OpenAI, DeepSeek, or Google APIs.
