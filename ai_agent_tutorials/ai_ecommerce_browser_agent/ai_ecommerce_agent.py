# sudoku_agent.py
from phi.agent import Agent
from phi.model.deepseek import DeepSeekChat
from phi.tools import ToolRegistry
from sudoku import Sudoku
import json
import time

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
        if self.initial_board[row][col] != 0:
            return False
        if number in self.puzzle.board[row]:
            return False
        if number in [self.puzzle.board[i][col] for i in range(9)]:
            return False
        start_row, start_col = 3*(row//3), 3*(col//3)
        for i in range(3):
            for j in range(3):
                if self.puzzle.board[start_row+i][start_col+j] == number:
                    return False
        return True

    def make_move(self, row: int, col: int, number: int) -> dict:
        """Apply move with clear error messages"""
        try:
            if not (0 <= row <= 8 and 0 <= col <= 8):
                return {"valid": False, "message": "Coordinates must be 0-8"}
            
            if not (1 <= number <= 9):
                return {"valid": False, "message": "Number must be 1-9"}
            
            if self.initial_board[row][col] != 0:
                return {"valid": False, "message": "Cannot modify initial clue"}
            
            if not self.is_valid_move(row, col, number):
                return {"valid": False, "message": "Violates Sudoku rules"}
            
            self.puzzle.board[row][col] = number
            return {"valid": True, "message": "Valid move"}
        
        except Exception as e:
            return {"valid": False, "message": f"System error: {str(e)}"}

class SudokuTools(ToolRegistry):
    def __init__(self):
        super().__init__(name="sudoku_tools")
        self.game = SudokuGame(difficulty=0.5)
        self.register(self.get_board)
        self.register(self.make_move)

    def get_board(self) -> str:
        return json.dumps({
            "board": self.game.get_board(),
            "instructions": "0 = empty cell (.), 1-9 = numbers"
        })

    def make_move(self, arguments: str) -> str:
        """Handle JSON input with validation"""
        try:
            data = json.loads(arguments)
            result = self.game.make_move(
                int(data["row"]),
                int(data["col"]),
                int(data["number"])
            )
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "valid": False,
                "message": f"Invalid request format: {str(e)}"
            })

def print_board(board: list):
    """Display board with . for empty cells"""
    print("\nCurrent Sudoku:")
    for i, row in enumerate(board):
        if i % 3 == 0 and i != 0:
            print("------+-------+------")
        displayed = ["." if num == 0 else str(num) for num in row]
        print(" ".join(displayed[0:3]), end=" | ")
        print(" ".join(displayed[3:6]), end=" | ")
        print(" ".join(displayed[6:9]))

sudoku_agent = Agent(
    model=DeepSeekChat(
        id="deepseek-chat",
        api_key="sk-",
        temperature=0.0
    ),
    tools=[SudokuTools()],
    system_prompt="""You are a Sudoku expert. Follow these rules:

    1. GOAL: Fill empty cells (marked . or 0) with 1-9
    2. RULES:
       - No duplicates in rows/columns/3x3 boxes
       - Never modify initial numbers
    3. RESPONSE FORMAT:
       a. Analyze current board
       b. Identify next best move
       c. Output JSON: {"row": 0-8, "col": 0-8, "number": 1-9}
    4. ERROR HANDLING:
       - If move fails, analyze why and try again""",
    instructions=[
        "First: Find empty cells (0 or .)",
        "Second: Check row/column/box constraints",
        "Third: Start with cells having fewest options",
        "Fourth: Validate move before submitting",
        "Fifth: If error occurs, debug and retry"
    ],
    show_tool_calls=True,
    debug_mode=True
)

def main():
    print("Starting Sudoku Solver with DeepSeek-R1")
    tools = SudokuTools()
    
    # Initial state
    current_board = json.loads(tools.get_board())["board"]
    print_board(current_board)
    
    # Solving loop
    max_steps = 30
    for step in range(1, max_steps + 1):
        print(f"\n--- Step {step} ---")
        start_time = time.time()
        
        try:
            response = sudoku_agent.run("Analyze and make next move")
            print(f"\nResponse received in {time.time()-start_time:.2f}s")
            print(f"AI Response:\n{response}")
            
            # Update and display board
            current_board = json.loads(tools.get_board())["board"]
            print_board(current_board)
            
            # Check solution
            if all(0 not in row for row in current_board):
                print("\n✅ Sudoku Solved Successfully!")
                break
                
        except Exception as e:
            print(f"🚨 Error: {str(e)}")
            break

if __name__ == "__main__":
    main()