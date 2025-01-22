# sudoku_agent.py
from phi.agent import Agent
from phi.model.deepseek import DeepSeekChat
from phi.tools import ToolRegistry
from sudoku import Sudoku
import json

class SudokuGame:
    def __init__(self, difficulty=0.5):
        """Initialize Sudoku puzzle with validation"""
        self.puzzle = Sudoku(3).difficulty(difficulty)
        self.solution = self.puzzle.solve()
        self.initial_board = [[num or 0 for num in row] for row in self.puzzle.board]
        self.puzzle.board = [row.copy() for row in self.initial_board]

    def get_board(self) -> list:
        """Return current board state with 0 for empty cells"""
        return [[num or 0 for num in row] for row in self.puzzle.board]

    def is_valid_move(self, row: int, col: int, number: int) -> bool:
        """Validate move against Sudoku rules"""
        # Check initial clues
        if self.initial_board[row][col] != 0:
            return False

        # Check row
        if number in [x for x in self.puzzle.board[row] if x]:
            return False

        # Check column
        if number in [self.puzzle.board[i][col] for i in range(9) if self.puzzle.board[i][col]]:
            return False

        # Check 3x3 box
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(3):
            for j in range(3):
                if self.puzzle.board[start_row+i][start_col+j] == number:
                    return False
        return True

    def make_move(self, row: int, col: int, number: int) -> dict:
        """Apply move with full validation"""
        try:
            if not (1 <= number <= 9):
                return {"valid": False, "message": "Number must be 1-9"}

            if not self.is_valid_move(row, col, number):
                return {"valid": False, "message": "Violates Sudoku rules"}

            self.puzzle.board[row][col] = number
            return {"valid": True, "message": "Valid move"}

        except IndexError:
            return {"valid": False, "message": "Invalid coordinates"}

class SudokuTools(ToolRegistry):
    def __init__(self):
        super().__init__(name="sudoku_tools")
        self.game = SudokuGame(difficulty=0.5)
        self.register(self.get_board)
        self.register(self.make_move)

    def get_board(self) -> str:
        return json.dumps({"board": self.game.get_board()})

    def make_move(self, row: int, col: int, number: int) -> str:
        result = self.game.make_move(row, col, number)
        return json.dumps(result)

def is_solved(board: list) -> bool:
    """Check if board is fully solved according to Sudoku rules"""
    # Check all cells filled
    if any(0 in row for row in board):
        return False

    # Validate all rows, columns and boxes
    for i in range(9):
        # Check rows
        if len(set(board[i])) != 9:
            return False
        # Check columns
        column = [board[j][i] for j in range(9)]
        if len(set(column)) != 9:
            return False

    # Check 3x3 boxes
    for i in range(0, 9, 3):
        for j in range(0, 9, 3):
            box = []
            for x in range(3):
                for y in range(3):
                    box.append(board[i+x][j+y])
            if len(set(box)) != 9:
                return False
    return True

def print_board(board: list):
    """Display Sudoku board with proper formatting"""
    print("\nCurrent Sudoku:")
    for i, row in enumerate(board):
        if i % 3 == 0 and i != 0:
            print("------+-------+------")
        row_str = [str(num) if num != 0 else "." for num in row]
        print(" ".join(row_str[0:3]), end=" | ")
        print(" ".join(row_str[3:6]), end=" | ")
        print(" ".join(row_str[6:9]))

sudoku_agent = Agent(
    model=DeepSeekChat(
        id="deepseek-chat",
        api_key="sk-",
        temperature=0.0
    ),
    tools=[SudokuTools()],
    system_prompt="""You are a Sudoku master. Strictly follow these rules:

    **Objective**:
    Fill all empty cells (marked 0) so that:
    1. Each row contains 1-9 with no repeats
    2. Each column contains 1-9 with no repeats
    3. Each 3x3 box contains 1-9 with no repeats

    **Constraints**:
    - Never modify initial numbers (non-zero values)
    - Use logical deduction only (no guessing)
    - Verify moves against all three rules before placing

    **Response Format**:
    1. Explain your reasoning
    2. Provide move in JSON format: {"row": 0-8, "col": 0-8, "number": 1-9}""",
    instructions=[
        "1. Analyze rows for missing numbers",
        "2. Check columns for conflicts",
        "3. Verify 3x3 box constraints",
        "4. Start with cells having fewest possibilities",
        "5. Double-check all three rules before placing",
        "6. If stuck, re-examine related rows/columns/boxes"
    ],
    show_tool_calls=True
)

def main():
    print("Starting Sudoku Solver with DeepSeek-R1")
    tools = SudokuTools()
    
    # Initial state
    current_board = json.loads(tools.get_board())["board"]
    print_board(current_board)
    
    # Solving loop
    max_steps = 40
    for step in range(1, max_steps + 1):
        print(f"\n--- Step {step} ---")
        
        try:
            response = sudoku_agent.run("Analyze and make next move")
            print(f"\nAI Response:\n{response}")
            
            # Get updated board
            current_board = json.loads(tools.get_board())["board"]
            print_board(current_board)
            
            # Check solution
            if is_solved(current_board):
                print("\n🎉 Sudoku Solved Successfully!")
                print("All rules verified:")
                print("- No row/column/box duplicates")
                print("- All cells filled correctly")
                break
                
        except Exception as e:
            print(f"Error: {str(e)}")
            break

if __name__ == "__main__":
    main()