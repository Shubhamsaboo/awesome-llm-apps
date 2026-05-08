import chess
import chess.svg
import streamlit as st
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_agentchat.conditions import MaxMessageTerm
import asyncio

if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = None
if "board" not in st.session_state:
    st.session_state.board = chess.Board()
if "made_move" not in st.session_state:
    st.session_state.made_move = False
if "board_svg" not in st.session_state:
    st.session_state.board_svg = None
if "move_history" not in st.session_state:
    st.session_state.move_history = []
if "max_turns" not in st.session_state:
    st.session_state.max_turns = 5

st.sidebar.title("Chess Agent Configuration")
openai_api_key = st.sidebar.text_input("Enter your OpenAI API key:", type="password")
if openai_api_key:
    st.session_state.openai_api_key = openai_api_key
    st.sidebar.success("API key saved!")

st.sidebar.info("""
For a complete chess game with potential checkmate, it would take max_turns > 200 approximately.
However, this will consume significant API credits and a lot of time.
For demo purposes, using 5-10 turns is recommended.
""")

max_turns_input = st.sidebar.number_input(
    "Enter the number of turns (max_turns):",
    min_value=1,
    max_value=1000,
    value=st.session_state.max_turns,
    step=1
)

if max_turns_input:
    st.session_state.max_turns = max_turns_input
    st.sidebar.success(f"Max turns of total chess moves set to {st.session_state.max_turns}!")

st.title("Chess with AG2 Agents")

def available_moves() -> str:
    available_moves = [str(move) for move in st.session_state.board.legal_moves]
    return "Available moves are: " + ",".join(available_moves)

def execute_move(move: str) -> str:
    try:
        chess_move = chess.Move.from_uci(move)
        if chess_move not in st.session_state.board.legal_moves:
            return f"Invalid move: {move}. Please call available_moves() to see valid moves."

        st.session_state.board.push(chess_move)
        st.session_state.made_move = True

        board_svg = chess.svg.board(st.session_state.board,
                                  arrows=[(chess_move.from_square, chess_move.to_square)],
                                  fill={chess_move.from_square: "gray"},
                                  size=400)
        st.session_state.board_svg = board_svg
        st.session_state.move_history.append(board_svg)

        moved_piece = st.session_state.board.piece_at(chess_move.to_square)
        piece_unicode = moved_piece.unicode_symbol()
        piece_type_name = chess.piece_name(moved_piece.piece_type)
        piece_name = piece_type_name.capitalize() if piece_unicode.isupper() else piece_type_name

        from_square = chess.SQUARE_NAMES[chess_move.from_square]
        to_square = chess.SQUARE_NAMES[chess_move.to_square]
        move_desc = f"Moved {piece_name} ({piece_unicode}) from {from_square} to {to_square}."
        if st.session_state.board.is_checkmate():
            winner = 'White' if st.session_state.board.turn == chess.BLACK else 'Black'
            move_desc += f"\nCheckmate! {winner} wins!"
        elif st.session_state.board.is_stalemate():
            move_desc += "\nGame ended in stalemate!"
        elif st.session_state.board.is_insufficient_material():
            move_desc += "\nGame ended - insufficient material to checkmate!"
        elif st.session_state.board.is_check():
            move_desc += "\nCheck!"

        return move_desc
    except ValueError:
        return f"Invalid move format: {move}. Please use UCI format (e.g., 'e2e4')."

if st.session_state.openai_api_key:
    try:
        tools = [
            {
                "name": "available_moves",
                "description": "Get list of legal chess moves",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "execute_move",
                "description": "Execute a chess move in UCI format (e.g., 'e2e4')",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "move": {
                            "type": "string",
                            "description": "The move in UCI format"
                        }
                    },
                    "required": ["move"]
                }
            }
        ]

        agent_white = AssistantAgent(
            name="Agent_White",
            model_client={
                "provider": "openai",
                "config": {
                    "model": "gpt-4o-mini",
                    "api_key": st.session_state.openai_api_key,
                }
            },
            tools=[],
            system_message="You are a professional chess player and you play as white. "
            "First call available_moves() first, to get list of legal available moves. "
            "Then call execute_move(move) to make a move.",
        )

        agent_black = AssistantAgent(
            name="Agent_Black",
            model_client={
                "provider": "openai",
                "config": {
                    "model": "gpt-4o-mini",
                    "api_key": st.session_state.openai_api_key,
                }
            },
            tools=[],
            system_message="You are a professional chess player and you play as black. "
            "First call available_moves() first, to get list of legal available moves. "
            "Then call execute_move(move) to make a move.",
        )

        st.info("""
This chess game is played between two AG2 AI agents:
- **Agent White**: A GPT-4o-mini powered chess player controlling white pieces
- **Agent Black**: A GPT-4o-mini powered chess player controlling black pieces

The game is managed by turn-taking between agents.
""")

        initial_board_svg = chess.svg.board(st.session_state.board, size=300)
        st.subheader("Initial Board")
        st.image(initial_board_svg)

        if st.button("Start Game"):
            st.session_state.board.reset()
            st.session_state.made_move = False
            st.session_state.move_history = []
            st.session_state.board_svg = chess.svg.board(st.session_state.board, size=300)
            st.info("The AI agents will now play against each other.")
            st.success("You can view the interaction between the agents in the terminal output.")
            st.write("Game started! White's turn.")

            async def play_game():
                results = []
                for turn in range(st.session_state.max_turns):
                    if turn % 2 == 0:
                        agent = agent_white
                        color = "White"
                    else:
                        agent = agent_black
                        color = "Black"

                    available = available_moves()
                    prompt = f"It's {color}'s turn. {available}. Make your move using execute_move()."

                    result = await agent.run(task=prompt)
                    results.append(f"{color}: {result.messages[-1].content}")

                    if st.session_state.board.is_game_over():
                        break

                return results

            with st.spinner("Agents are playing..."):
                results = asyncio.run(play_game())

            for result in results:
                st.write(result)

            st.subheader("Move History")
            for i, move_svg in enumerate(st.session_state.move_history):
                if i % 2 == 0:
                    move_by = "Agent White"
                else:
                    move_by = "Agent Black"

                st.write(f"Move {i + 1} by {move_by}")
                st.image(move_svg)

        if st.button("Reset Game"):
            st.session_state.board.reset()
            st.session_state.made_move = False
            st.session_state.move_history = []
            st.session_state.board_svg = None
            st.write("Game reset! Click 'Start Game' to begin a new game.")

    except Exception as e:
        st.error(f"An error occurred: {e}. Please check your API key and try again.")

else:
    st.warning("Please enter your OpenAI API key in the sidebar to start the game.")
