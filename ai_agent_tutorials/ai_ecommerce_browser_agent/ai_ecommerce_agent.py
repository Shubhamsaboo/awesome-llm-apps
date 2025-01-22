from phi.agent import Agent
from phi.model.deepseek import DeepSeekChat
from phi.tools import ToolRegistry
from sudoku import Sudoku
import json

# ================== Shared Tools ==================
class SudokuTools(ToolRegistry):
    def __init__(self):
        super().__init__(name="sudoku_tools")
        self.puzzle = None
        self.solution = None
        self.register(self.generate_puzzle)
        self.register(self.get_board)
        self.register(self.validate_solution)

    def generate_puzzle(self, difficulty: float = 0.5) -> str:
        """Generate a new Sudoku puzzle with valid difficulty"""
        try:
            # Ensure difficulty is between 0 and 1
            if not (0 < difficulty < 1):
                difficulty = 0.5  # Default to medium difficulty
                print("Warning: Difficulty reset to 0.5 (must be between 0 and 1)")
            
            self.puzzle = Sudoku(3).difficulty(difficulty)
            self.solution = self.puzzle.solve()
            return json.dumps({
                "puzzle": [[num or 0 for num in row] for row in self.puzzle.board],
                "solution": [[num or 0 for num in row] for row in self.solution.board]
            })
        except Exception as e:
            return json.dumps({"error": f"Failed to generate puzzle: {str(e)}"})

    def get_board(self) -> str:
        """Return current board state"""
        if not self.puzzle:
            return json.dumps({"error": "No puzzle generated"})
        return json.dumps({
            "board": [[num or 0 for num in row] for row in self.puzzle.board]
        })

    def validate_solution(self, board: str) -> str:
        """Validate the final solution"""
        try:
            board_data = json.loads(board)
            if not isinstance(board_data, list) or len(board_data) != 9:
                return json.dumps({"valid": False, "message": "Invalid board format"})
            
            # Check against solution
            if board_data == [[num or 0 for num in row] for row in self.solution.board]:
                return json.dumps({"valid": True, "message": "Solution is correct"})
            return json.dumps({"valid": False, "message": "Solution is incorrect"})
        except Exception as e:
            return json.dumps({"valid": False, "message": f"Validation error: {str(e)}"})

# ================== Helper Function ==================
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

# ================== Agent 1: Puzzle Analyzer ==================
puzzle_analyzer = Agent(
    model=DeepSeekChat(
        id="deepseek-chat",
        api_key="sk-",
        temperature=0.1
    ),
    tools=[SudokuTools()],
    system_prompt="""You are a Sudoku puzzle analyzer. Your tasks:
1. Generate a Sudoku puzzle with difficulty between 0 and 1
2. Analyze its difficulty
3. Prepare it for solving""",
    instructions=[
        "Use generate_puzzle with difficulty=0.5 (medium)",
        "Analyze the number of empty cells",
        "Estimate difficulty (easy/medium/hard)",
        "Format output for the solver agent"
    ]
)

# ================== Agent 2: Solver ==================
solver_agent = Agent(
    model=DeepSeekChat(
        id="deepseek-chat",
        api_key="sk-",
        temperature=0.0
    ),
    tools=[SudokuTools()],
    system_prompt="""You are a Sudoku solver. Follow these rules:
1. Analyze the current board state
2. Use logical deduction to fill empty cells
3. Validate each move against Sudoku rules
4. Format moves as {"row": 0-8, "col": 0-8, "number": 1-9}""",
    instructions=[
        "Start with cells having fewest possibilities",
        "Check row/column/box constraints",
        "If stuck, re-examine related cells",
        "Stop when all cells are filled"
    ]
)

# ================== Agent 3: Validator ==================
validator_agent = Agent(
    model=DeepSeekChat(
        id="deepseek-chat",
        api_key="sk-",
        temperature=0.0
    ),
    tools=[SudokuTools()],
    system_prompt="""You are a Sudoku validator. Your tasks:
1. Verify the final solution
2. Check for rule violations
3. Confirm puzzle completion""",
    instructions=[
        "Validate rows for duplicates",
        "Validate columns for duplicates",
        "Validate 3x3 boxes for duplicates",
        "Confirm all cells are filled"
    ]
)

# ================== Workflow Execution ==================
def main():
    print("Starting Multi-Agent Sudoku Solver...")
    tools = SudokuTools()
    
    # Step 1: Generate and analyze puzzle
    print("\n--- Step 1: Puzzle Analysis ---")
    puzzle_response = puzzle_analyzer.run("Generate and analyze a medium Sudoku puzzle with difficulty=0.5")
    print(f"Puzzle Analyzer Response:\n{puzzle_response.content}")
    
    # Display initial puzzle
    initial_board = json.loads(tools.get_board())["board"]
    print("\nInitial Sudoku Puzzle:")
    print_board(initial_board)
    
    # Step 2: Solve the puzzle
    print("\n--- Step 2: Solving ---")
    solver_response = solver_agent.run("Solve the Sudoku puzzle")
    print(f"Solver Agent Response:\n{solver_response.content}")
    
    # Display final solved puzzle
    final_board = json.loads(tools.get_board())["board"]
    print("\nFinal Solved Sudoku:")
    print_board(final_board)
    
    # Step 3: Validate the solution
    print("\n--- Step 3: Validation ---")
    validation_response = validator_agent.run(f"Validate this solution: {json.dumps(final_board)}")
    print(f"Validator Agent Response:\n{validation_response.content}")

if __name__ == "__main__":
    main()