from phi.agent import Agent
from phi.model.deepseek import DeepSeekChat
from phi.tools import ToolRegistry
from sudoku import Sudoku
import json

class SudokuTools(ToolRegistry):
    def __init__(self):
        super().__init__(name="sudoku_tools")
        self.puzzle = None
        self.solution = None

    def generate_puzzle(self, difficulty: float = 0.5) -> dict:
        """Generate a new Sudoku puzzle with valid difficulty"""
        try:
            if not (0 < difficulty < 1):
                difficulty = 0.5
                print("Warning: Difficulty reset to 0.5 (must be between 0 and 1)")
            
            sudoku = Sudoku(3).difficulty(difficulty)
            self.puzzle = [[num or 0 for num in row] for row in sudoku.board]
            self.solution = [[num or 0 for num in row] for row in sudoku.solve().board]
            return {
                "puzzle": self.puzzle,
                "solution": self.solution
            }
        except Exception as e:
            return {"error": str(e)}

# Create Sudoku Tools instance
sudoku_tools = SudokuTools()

# ================== Agent 1: Solver ==================
solver_agent = Agent(
    model=DeepSeekChat(
        id="deepseek-reasoner",
        api_key="sk-",
        temperature=0.0
    ),
    system_prompt="""You are a Sudoku solving expert. The Goal is to give a final sudoku grid solving the puzzle. Rules:
1. Input is a 9x9 matrix with 0s for empty cells
2. Solve using logical deduction only
3. Each row MUST contain numbers 1-9 exactly once
4. Each column MUST contain numbers 1-9 exactly once
5. Each 3x3 box MUST contain numbers 1-9 exactly once
6. Return the completed grid in a clear format with one row per line
7. Double check your solution before returning it""",
    instructions=[
        "1. Analyze the input grid",
        "2. Fill empty cells (0s) following strict Sudoku rules",
        "3. Validate each number placement ensures no duplicates in rows/columns/boxes",
        "4. Double check the entire solution",
        "5. Return the solved grid with one row per line"
    ],
    stream=True,
    debug_mode=True,
)

# ================== Agent 2: Validator ==================
validator_agent = Agent(
    model=DeepSeekChat(
        id="deepseek-chat",
        api_key="sk-",
        temperature=0.0
    ),
    system_prompt="""You are a Sudoku solution validator.The Goal is to give a final sudoku grid solving the puzzle. Check:
1. All numbers 1-9 in rows
2. All numbers 1-9 in columns
3. All numbers 1-9 in 3x3 boxes
4. No duplicate numbers""",
    instructions=[
        "1. Verify all rows contain 1-9",
        "2. Verify all columns contain 1-9",
        "3. Verify all 3x3 boxes contain 1-9",
        "4. Return validation result"
    ]
)

def print_sudoku(grid: list, title: str = "Sudoku"):
    """Print Sudoku grid from 2D list"""
    print(f"\n{title}:")
    for i, row in enumerate(grid):
        if i % 3 == 0 and i != 0:
            print("------+-------+------")
        print(" ".join(str(num) if num != 0 else "." for num in row[0:3]), end=" | ")
        print(" ".join(str(num) if num != 0 else "." for num in row[3:6]), end=" | ")
        print(" ".join(str(num) if num != 0 else "." for num in row[6:9]))

def extract_grid_from_text(text: str) -> list[list[int]]:
    """Extract 9x9 grid from agent's response text"""
    grid = []
    for line in text.split('\n'):
        # Look for lines with numbers and convert to list of integers
        if any(c.isdigit() for c in line):
            row = [int(c) for c in line if c.isdigit()]
            if len(row) == 9:  # Only accept valid rows
                grid.append(row)
    return grid if len(grid) == 9 else None

def main():
    print("Starting Sudoku Workflow...")
    
    # Step 1: Generate puzzle directly
    print("\n--- Step 1: Puzzle Generation ---")
    puzzle_data = sudoku_tools.generate_puzzle(difficulty=0.5)
    sudoku_grid = puzzle_data["puzzle"]
    print_sudoku(sudoku_grid, "Initial Puzzle")
    
    # Step 2: Solve puzzle
    print("\n--- Step 2: Solving ---")
    solve_response = solver_agent.run(f"Solve this Sudoku: {sudoku_grid}", stream=True)
    
    # Handle streaming response
    solution_text = ""
    for chunk in solve_response:
        if hasattr(chunk, 'content'):
            solution_text += chunk.content
        print(chunk, end="", flush=False)
    
    # Extract and display the solved grid
    solved_grid = extract_grid_from_text(solution_text)
    if solved_grid:
        print_sudoku(solved_grid, "Final Solved Puzzle")
        
        # Step 3: Validate solution
        print("\n--- Step 3: Validation ---")
        validation_prompt = f"""Please validate this Sudoku solution:
{solved_grid}

Check and confirm:
1. Each row contains numbers 1-9 exactly once
2. Each column contains numbers 1-9 exactly once
3. Each 3x3 box contains numbers 1-9 exactly once
4. No duplicate numbers in any row, column, or box

Return VALID if all checks pass, or list the specific violations found."""

        validation_response = validator_agent.run(validation_prompt, stream=False)
        print("Validation Result:", validation_response.content)
    else:
        print("\nError: Could not extract valid solution from agent's response")

if __name__ == "__main__":
    main()