# AI Chess Game - Autogen

This is a simple Chess game that uses an AI agents - Player black and player white to play the game. There's also a board proxy agent to execute the tools and manage the game. It is important to use a board proxy as a non-LLM "guard rail" to ensure the game is played correctly and to prevent agents from making illegal moves.


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