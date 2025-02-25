from typing import List, Optional, Tuple

import streamlit as st

# Define constants for players
X_PLAYER = "X"
O_PLAYER = "O"
EMPTY = " "


class TicTacToeBoard:
    def __init__(self):
        # Initialize empty 3x3 board
        self.board = [[EMPTY for _ in range(3)] for _ in range(3)]
        self.current_player = X_PLAYER

    def make_move(self, row: int, col: int) -> Tuple[bool, str]:
        """
        Make a move on the board.

        Args:
            row (int): Row index (0-2)
            col (int): Column index (0-2)

        Returns:
            Tuple[bool, str]: (Success status, Message with current board state or error)
        """
        # Validate move coordinates
        if not (0 <= row <= 2 and 0 <= col <= 2):
            return (
                False,
                "Invalid move: Position out of bounds. Please choose row and column between 0 and 2.",
            )

        # Check if position is already occupied
        if self.board[row][col] != EMPTY:
            return False, f"Invalid move: Position ({row}, {col}) is already occupied."

        # Make the move
        self.board[row][col] = self.current_player

        # Get board state
        board_state = self.get_board_state()

        # Switch player
        self.current_player = O_PLAYER if self.current_player == X_PLAYER else X_PLAYER

        return True, f"Move successful!\n{board_state}"

    def get_board_state(self) -> str:
        """
        Returns a string representation of the current board state.
        """
        board_str = "\n-------------\n"
        for row in self.board:
            board_str += f"| {' | '.join(row)} |\n-------------\n"
        return board_str

    def check_winner(self) -> Optional[str]:
        """
        Check if there's a winner.

        Returns:
            Optional[str]: The winning player (X or O) or None if no winner
        """
        # Check rows
        for row in self.board:
            if row.count(row[0]) == 3 and row[0] != EMPTY:
                return row[0]

        # Check columns
        for col in range(3):
            column = [self.board[row][col] for row in range(3)]
            if column.count(column[0]) == 3 and column[0] != EMPTY:
                return column[0]

        # Check diagonals
        diagonal1 = [self.board[i][i] for i in range(3)]
        if diagonal1.count(diagonal1[0]) == 3 and diagonal1[0] != EMPTY:
            return diagonal1[0]

        diagonal2 = [self.board[i][2 - i] for i in range(3)]
        if diagonal2.count(diagonal2[0]) == 3 and diagonal2[0] != EMPTY:
            return diagonal2[0]

        return None

    def is_board_full(self) -> bool:
        """
        Check if the board is full (draw condition).
        """
        return all(cell != EMPTY for row in self.board for cell in row)

    def get_valid_moves(self) -> List[Tuple[int, int]]:
        """
        Get a list of valid moves (empty positions).

        Returns:
            List[Tuple[int, int]]: List of (row, col) tuples representing valid moves
        """
        valid_moves = []
        for row in range(3):
            for col in range(3):
                if self.board[row][col] == EMPTY:
                    valid_moves.append((row, col))
        return valid_moves

    def get_game_state(self) -> Tuple[bool, str]:
        """
        Get the current game state.

        Returns:
            Tuple[bool, str]: (is_game_over, status_message)
        """
        winner = self.check_winner()
        if winner:
            return True, f"Player {winner} wins!"

        if self.is_board_full():
            return True, "It's a draw!"

        return False, "Game in progress"


def display_board(board: TicTacToeBoard):
    """Display the Tic Tac Toe board using Streamlit"""
    board_html = '<div class="game-board">'

    for i in range(3):
        for j in range(3):
            cell_value = board.board[i][j]
            board_html += f'<div class="board-cell">{cell_value}</div>'

    board_html += "</div>"
    st.markdown(board_html, unsafe_allow_html=True)


def show_agent_status(agent_name: str, status: str):
    """Display the current agent status"""
    st.markdown(
        f"""<div class="agent-status">
            🤖 <b>{agent_name}</b>: {status}
        </div>""",
        unsafe_allow_html=True,
    )


def create_mini_board_html(
    board_state: list, highlight_pos: tuple = None, is_player1: bool = True
) -> str:
    """Create HTML for a mini board with player-specific highlighting"""
    html = '<div class="mini-board">'
    for i in range(3):
        for j in range(3):
            highlight = (
                f"highlight player{1 if is_player1 else 2}"
                if highlight_pos and (i, j) == highlight_pos
                else ""
            )
            html += f'<div class="mini-cell {highlight}">{board_state[i][j]}</div>'
    html += "</div>"
    return html


def display_move_history():
    """Display the move history with mini boards in two columns"""
    st.markdown(
        '<h3 style="margin-bottom: 30px;">📜 Game History</h3>',
        unsafe_allow_html=True,
    )
    history_container = st.empty()

    if "move_history" in st.session_state and st.session_state.move_history:
        # Split moves into player 1 and player 2 moves
        p1_moves = []
        p2_moves = []
        current_board = [[" " for _ in range(3)] for _ in range(3)]

        # Process all moves first
        for move in st.session_state.move_history:
            row, col = map(int, move["move"].split(","))
            is_player1 = "Player 1" in move["player"]
            symbol = "X" if is_player1 else "O"
            current_board[row][col] = symbol
            board_copy = [row[:] for row in current_board]

            move_html = f"""<div class="move-entry player{1 if is_player1 else 2}">
                {create_mini_board_html(board_copy, (row, col), is_player1)}
                <div class="move-info">
                    <div class="move-number player{1 if is_player1 else 2}">Move #{move["number"]}</div>
                    <div>{move["player"]}</div>
                    <div style="font-size: 0.9em; color: #888">Position: ({row}, {col})</div>
                </div>
            </div>"""

            if is_player1:
                p1_moves.append(move_html)
            else:
                p2_moves.append(move_html)

        max_moves = max(len(p1_moves), len(p2_moves))
        history_content = '<div class="history-grid">'

        # Left column (Player 1)
        history_content += '<div class="history-column-left">'
        for i in range(max_moves):
            entry_html = ""
            # Player 1 move
            if i < len(p1_moves):
                entry_html += p1_moves[i]
            history_content += entry_html
        history_content += "</div>"

        # Right column (Player 2)
        history_content += '<div class="history-column-right">'
        for i in range(max_moves):
            entry_html = ""
            # Player 2 move
            if i < len(p2_moves):
                entry_html += p2_moves[i]
            history_content += entry_html
        history_content += "</div>"

        history_content += "</div>"

        # Display the content
        history_container.markdown(history_content, unsafe_allow_html=True)
    else:
        history_container.markdown(
            """<div style="text-align: center; color: #666; padding: 20px;">
                No moves yet. Start the game to see the history!
            </div>""",
            unsafe_allow_html=True,
        )


CUSTOM_CSS = """
<style>
/* Main Styles */
.main-title {
    text-align: center;
    background: linear-gradient(45deg, #FF4B2B, #FF416C);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3em;
    font-weight: bold;
    padding: 0.5em 0;
}
.subtitle {
    text-align: center;
    color: #666;
    margin-bottom: 1em;
}
.game-board {
    display: grid;
    grid-template-columns: repeat(3, 80px);
    gap: 5px;
    justify-content: center;
    margin: 1em auto;
    background: #666;
    padding: 5px;
    border-radius: 8px;
    width: fit-content;
}
.board-cell {
    width: 80px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2em;
    font-weight: bold;
    background-color: #2b2b2b;
    color: #fff;
    transition: all 0.3s ease;
    margin: 0;
    padding: 0;
}
.board-cell:hover {
    background-color: #3b3b3b;
}
.agent-status {
    background-color: #1e1e1e;
    border-left: 4px solid #4CAF50;
    padding: 10px;
    margin: 10px auto;
    border-radius: 4px;
    max-width: 600px;
    text-align: center;
}
.agent-thinking {
    display: flex;
    justify-content: center;
    background-color: #2b2b2b;
    padding: 10px;
    border-radius: 5px;
    margin: 10px auto;
    border-left: 4px solid #FFA500;
    max-width: 600px;
}
.move-history {
    background-color: #2b2b2b;
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
}
.thinking-container {
    position: fixed;
    bottom: 20px;
    left: 50%;
    z-index: 1000;
    min-width: 300px;
}
.agent-thinking {
    background-color: rgba(43, 43, 43, 0.95);
    border: 1px solid #4CAF50;
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
}

/* Move History Updates */
.history-header {
    text-align: center;
    margin-bottom: 30px;
}

.history-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px; /* Controls spacing between columns */
    width: 100%;
    margin: 0; /* Remove left/right margins */
    padding: 0;
}

.history-column-left,
.history-column-right {
    display: flex;
    flex-direction: column;
    align-items: flex-start; /* Ensures columns fill available space nicely */
    margin: 0;
    padding: 0;
    width: 100%;
}

.move-entry {
    display: flex;
    align-items: center;
    padding: 12px;
    margin: 8px 0;
    background-color: #2b2b2b;
    border-radius: 4px;
    width: 100%; /* Removed fixed width so entries span the column */
    box-sizing: border-box;
}

.move-entry.player1 {
    border-left: 4px solid #4CAF50;
}

.move-entry.player2 {
    border-left: 4px solid #f44336;
}

/* Mini-board styling inside moves */
.mini-board {
    display: grid;
    grid-template-columns: repeat(3, 25px);
    gap: 2px;
    background: #444;
    padding: 2px;
    border-radius: 4px;
    margin-right: 15px;
}

.mini-cell {
    width: 25px;
    height: 25px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: bold;
    background-color: #2b2b2b;
    color: #fff;
}

.mini-cell.highlight.player1 {
    background-color: #4CAF50;
    color: white;
}

.mini-cell.highlight.player2 {
    background-color: #f44336;
    color: white;
}

/* Move info styling */
.move-info {
    flex-grow: 1;
    padding-left: 12px;
}

.move-number {
    font-weight: bold;
    margin-right: 10px;
}

.move-number.player1 {
    color: #4CAF50;
}

.move-number.player2 {
    color: #f44336;
}
</style>
"""
