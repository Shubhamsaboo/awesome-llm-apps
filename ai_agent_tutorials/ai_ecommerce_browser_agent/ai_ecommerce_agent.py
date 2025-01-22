# sudoku_agent.py
from phi.agent import Agent
from phi.model.deepseek import DeepSeekChat
from phi.tools import ToolRegistry
from sudoku import Sudoku
import json

class SudokuGame:
    def __init__(self, difficulty=0.5):
        """Initialize a Sudoku puzzle with specified difficulty"""
        self.puzzle = Sudoku(3).difficulty(difficulty)
        self.solution = self.puzzle.solve()
        self.initial_board = [row.copy() for row in self.puzzle.board]
    
    def get_board(self) -> list:
        """Return current board state"""
        return self.puzzle.board
    
    def make_move(self, row: int, col: int, number: int) -> dict:
        """Validate and apply a move"""
        try:
            if self.initial_board[row][col] != 0:
                return {"valid": False, "message": "Cannot modify initial clue"}
                
            if self.puzzle.board[row][col] != 0:
                return {"valid": False, "message": "Cell already filled"}
            
            if number == self.solution.board[row][col]:
                self.puzzle.board[row][col] = number
                return {"valid": True, "message": "Correct move!"}
            
            return {"valid": False, "message": "Incorrect move"}
            
        except IndexError:
            return {"valid": False, "message": "Invalid coordinates"}

class SudokuTools(ToolRegistry):
    def __init__(self):
        super().__init__(name="sudoku_tools")
        self.game = SudokuGame(difficulty=0.5)
        self.register(self.get_board)
        self.register(self.make_move)
        self.register(self.show_solution)

    def get_board(self) -> str:
        """Return current board as JSON string"""
        return json.dumps({"board": self.game.get_board()})

    def make_move(self, row: int, col: int, number: int) -> str:
        """Handle move request"""
        result = self.game.make_move(row, col, number)
        return json.dumps(result)

    def show_solution(self) -> str:
        """Return solution board"""
        return json.dumps({"solution": self.game.solution.board})

# Initialize the agent
sudoku_agent = Agent(
    model=DeepSeekChat(
        id="deepseek-chat",
        api_key="sk-",
        temperature=0.1
    ),
    tools=[SudokuTools()],
    system_prompt="""You are a Sudoku expert. Follow these rules:
1. Analyze the current board state
2. Suggest moves in format: {"row": 0-8, "col": 0-8, "number": 1-9}
3. Explain your reasoning step-by-step
4. Check moves against Sudoku rules""",
    instructions=[
        "Start with get_board to understand current state",
        "Prioritize empty cells with fewest possibilities",
        "Verify row, column, and 3x3 box constraints",
        "If stuck, use show_solution for reference",
        "Format responses clearly with reasoning first"
    ],
    show_tool_calls=True
)

def print_board(board: list):
    """Display Sudoku board in console"""
    print("\nCurrent Sudoku:")
    for i, row in enumerate(board):
        if i % 3 == 0 and i != 0:
            print("------+-------+------")
        print(" ".join(str(n) if n != 0 else "." for n in row[0:3]), end=" | ")
        print(" ".join(str(n) if n != 0 else "." for n in row[3:6]), end=" | ")
        print(" ".join(str(n) if n != 0 else "." for n in row[6:9]))

def main():
    print("Starting Sudoku Solver with DeepSeek-R1")
    tools = SudokuTools()
    
    # Initial state
    initial_board = json.loads(tools.get_board())["board"]
    print_board(initial_board)
    
    # Solving loop
    max_steps = 30
    for step in range(1, max_steps + 1):
        print(f"\n--- Step {step} ---")
        
        try:
            response = sudoku_agent.run("Analyze and suggest next move")
            print(f"\nAI Response:\n{response.content}")
            
            current_board = json.loads(tools.get_board())["board"]
            print_board(current_board)
            
            if all(0 not in row for row in current_board):
                print("\n🎉 Sudoku Solved Successfully!")
                break
                
        except Exception as e:
            print(f"Error: {str(e)}")
            break

if __name__ == "__main__":
    main()