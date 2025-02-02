import re
import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.deepseek import DeepSeek
from agno.models.google import Gemini

# Streamlit App Title
st.title("🎮 Agent X vs Agent O: Tic-Tac-Toe Game")

# Enhanced Welcome Message
with st.chat_message("assistant"):
    st.markdown("""
        **Welcome to the Tic-Tac-Toe AI Battle!** 🎮  
        This project pits two advanced AI agents against each other in a classic game of Tic-Tac-Toe.  
        Here's what you need to know:
    """)
    st.info("""
        - **Player X**: Powered by Google's Gemini Flash 2.0.  
        - **Player O**: Powered by DeepSeek v3.  
        - **How to Play**: Enter your API keys in the sidebar, click **Start Game**, and watch the AI battle it out!  
        - **Goal**: The first player to get three of their symbols in a row (horizontally, vertically, or diagonally) wins.  
        - **Draw**: If the board fills up without a winner, the game ends in a draw.  
    """)
    st.markdown("Ready to see who wins? Click the **Start Game** button below! 🚀")

# Initialize the game board in session state
if 'board' not in st.session_state:
    st.session_state.board = [[None, None, None],
                              [None, None, None],
                              [None, None, None]]

# Function to display the board with better styling
def display_board(board):
    st.markdown("""
        <style>
        .board {
            display: grid;
            grid-template-columns: repeat(3, 50px);
            grid-template-rows: repeat(3, 50px);
            gap: 5px;
            margin-bottom: 20px;
        }
        .cell {
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #ccc;
            font-size: 20px;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    st.write("Current Board:")
    board_html = '<div class="board">'
    for row in board:
        for cell in row:
            cell_value = cell if cell is not None else "&nbsp;"
            board_html += f'<div class="cell">{cell_value}</div>'
    board_html += '</div>'
    st.markdown(board_html, unsafe_allow_html=True)

# Function to get the board state as a string
def get_board_state(board):
    rows = []
    for i, row in enumerate(board):
        row_str = " | ".join([f"({i},{j}) {cell or ' '}" for j, cell in enumerate(row)])
        rows.append(f"Row {i}: {row_str}")
    return "\n".join(rows)

# Function to check for a winner
def check_winner(board):
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] and row[0] is not None:
            return row[0]
    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] and board[0][col] is not None:
            return board[0][col]
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] is not None:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] is not None:
        return board[0][2]
    # Check for draw
    if all(cell is not None for row in board for cell in row):
        return "Draw"
    return None

# Sidebar for API keys
st.sidebar.header("API Keys")
openai_api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
deepseek_api_key = st.sidebar.text_input("Enter your DeepSeek API Key", type="password")
google_api_key = st.sidebar.text_input("Enter your Google API Key (for Gemini)", type="password")

if openai_api_key:
    st.session_state.openai_api_key = openai_api_key
if deepseek_api_key:
    st.session_state.deepseek_api_key = deepseek_api_key
if google_api_key:
    st.session_state.google_api_key = google_api_key

# Initialize agents if API keys are provided
if 'openai_api_key' in st.session_state:
    player_x = Agent(
        name="Player X",
        model=Gemini(id="gemini-2.0-flash-exp", api_key=st.session_state.google_api_key),
        instructions=[
            "You are a Tic-Tac-Toe player using the symbol 'X'.",
            "Your opponent is using the symbol 'O'. Block their potential winning moves.",
            "Make your move in the format 'row, col' based on the current board state.",
            "Strategize to win by placing your symbol in a way that blocks your opponent from forming a straight line.",
            "Do not include any explanations or extra text. Only provide the move.",
            "Row and column indices start from 0.",
        ],
        markdown=True,
    )

    # Initialize Player O with DeepSeek or Google Gemini
    if 'deepseek_api_key' in st.session_state:
        player_o = Agent(
            name="Player O",
            model=DeepSeek(id="deepseek-chat", api_key=st.session_state.deepseek_api_key),
            instructions=[
                "You are a Tic-Tac-Toe player using the symbol 'O'.",
                "Your opponent is using the symbol 'X'. Block their potential winning moves.",
                "Make your move in the format 'row, col' based on the current board state.",
                "Strategize to win by placing your symbol in a way that blocks your opponent from forming a straight line.",
                "Do not include any explanations or extra text. Only provide the move.",
                "Row and column indices start from 0.",
            ],
            markdown=True,
        )
    else:
        st.warning("Please provide either a DeepSeek API key or a Google API key for Player O.")

    judge = Agent(
        name="Judge",
        model=OpenAIChat(id="gpt-4o", temperature=0.1, api_key=st.session_state.openai_api_key),
        instructions=[
            "You are the judge of a Tic-Tac-Toe game.",
            "The board is presented as rows with positions separated by '|'.",
            "Rows are labeled from 0 to 2, and columns from 0 to 2.",
            "Example board state:",
            "Row 0: (0,0) X | (0,1)   | (0,2) O",
            "Row 1: (1,0) O | (1,1) X | (1,2) X",
            "Row 2: (2,0) X | (2,1) O | (2,2) O",
            "Determine the winner based on this board state.",
            "The winner is the player with three of their symbols in a straight line (row, column, or diagonal).",
            "If the board is full and there is no winner, declare a draw.",
            "Provide only the result (e.g., 'Player X wins', 'Player O wins', 'Draw').",
        ],
        markdown=True,
    )

    # Function to extract the move from the agent's response
    def extract_move(response):
        content = response.content.strip()
        match = re.search(r'\d\s*,\s*\d', content)
        if match:
            move = match.group().replace(' ', '')
            return move
        numbers = re.findall(r'\d+', content)
        if len(numbers) >= 2:
            row = int(numbers[0])
            col = int(numbers[1])
            return f"{row},{col}"
        return None

    # Game loop
    def play_game():
        if 'current_player' not in st.session_state:
            st.session_state.current_player = player_x
        if 'symbol' not in st.session_state:
            st.session_state.symbol = "X"
        if 'move_count' not in st.session_state:
            st.session_state.move_count = 0

        max_moves = 9
        winner = None  # Initialize winner variable

        while st.session_state.move_count < max_moves:
            # Display the board
            display_board(st.session_state.board)

            # Prepare the board state for the agent
            board_state = get_board_state(st.session_state.board)
            move_prompt = (
                f"Current board state:\n{board_state}\n"
                f"{st.session_state.current_player.name}'s turn. Make your move in the format 'row, col'."
            )

            # Get the current player's move
            with st.chat_message("assistant"):
                st.write(f"**{st.session_state.current_player.name}'s turn:**")
                move_response = st.session_state.current_player.run(move_prompt)
                st.code(f"Agent {st.session_state.current_player.name} response:\n{move_response.content}", language="markdown")
                move = extract_move(move_response)
                st.write(f"**Extracted move:** {move}")

            if move is None:
                st.error("Invalid move! Please use the format 'row, col'.")
                continue

            try:
                row, col = map(int, move.split(','))
                if st.session_state.board[row][col] is not None:
                    st.error("Invalid move! Cell already occupied.")
                    continue
                st.session_state.board[row][col] = st.session_state.symbol
            except (ValueError, IndexError):
                st.error("Invalid move! Please use the format 'row, col'.")
                continue

            # Check for a winner or draw
            winner = check_winner(st.session_state.board)
            if winner:
                break  # Exit the loop if there's a winner

            # Switch players
            st.session_state.current_player = player_o if st.session_state.current_player == player_x else player_x
            st.session_state.symbol = "O" if st.session_state.symbol == "X" else "X"
            st.session_state.move_count += 1

        # After the game loop, display the final board and involve the judge agent
        st.write("**Final Board:**")
        display_board(st.session_state.board)

        if winner:
            st.success(f"**Result:** {winner}")
        else:
            st.success("**Result:** Draw")

        # Judge's announcement
        st.write("\n**Game Over. Judge is determining the result...**")
        st.write("**Final board state passed to judge:**")
        st.code(get_board_state(st.session_state.board), language="markdown")
        judge_prompt = (
            f"Final board state:\n{get_board_state(st.session_state.board)}\n"
            f"Determine the winner and announce the result."
        )
        judge_response = judge.run(judge_prompt)
        st.code(f"Judge's raw response:\n{judge_response.content}", language="markdown")
        announcement = judge_response.content.strip()
        st.success(f"**Judge's Announcement:** {announcement}")

    # Start Game Button
    if st.button("Start Game"):
        st.session_state.board = [[None, None, None],
                                  [None, None, None],
                                  [None, None, None]]
        st.session_state.current_player = player_x
        st.session_state.symbol = "X"
        st.session_state.move_count = 0
        play_game()
else:
    st.warning("Please enter your OpenAI API key and either Deepseek/Gemini API key to start the game.")