# AI Chess Game - Autogen

This is a simple Chess game that uses an AI agents - Player black and player white to play the game. There's also a board proxy agent to execute the tools and manage the game. It is important to use a board proxy as a non-LLM "guard rail" to ensure the game is played correctly and to prevent agents from making illegal moves.

Two agents (player_white and player_black) are initialized using the OpenAI API key. These agents are configured to play chess as white and black, respectively.
A board_proxy agent is created to manage the board state and validate moves.
Functions (make_move and available_moves) are registered with the agents to allow them to interact with the board.


### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd ai_agent_tutorials/ai_chess_game
```
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```
3. Get your OpenAI API Key

- Sign up for an [OpenAI account](https://platform.openai.com/) (or the LLM provider of your choice) and obtain your API key.

4. Run the Streamlit App
```bash
streamlit run ai_chess_agents.py
```

## Requirements

-   autogen
-   numpy
-   openai
-   streamlit
-   chess