from phi.agent import Agent
from phi.model.deepseek import DeepSeekChat
from phi.tools import ToolRegistry
from typing import Optional, List
import time

class SudokuGame:
    def __init__(self, puzzle: List[List[int]]):
        self.initial_puzzle = [row[:] for row in puzzle]
        self.solution = [row[:] for row in puzzle]
        self.steps = []

    def is_valid(self, row: int, col: int, num: int) -> bool:
        if num in self.solution[row]:
            return False
        if num in [self.solution[i][col] for i in range(9)]:
            return False
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(3):
            for j in range(3):
                if self.solution[start_row + i][start_col + j] == num:
                    return False
        return True

    def update_cell(self, row: int, col: int, num: int) -> bool:
        if self.initial_puzzle[row][col] == 0 and self.is_valid(row, col, num):
            self.solution[row][col] = num
            self.steps.append((row, col, num, "valid"))
            return True
        self.steps.append((row, col, num, "invalid"))
        return False

    def is_solved(self) -> bool:
        for row in self.solution:
            if 0 in row:
                return False
        return True

class SudokuTools(ToolRegistry):
    def __init__(self):
        super().__init__(name="sudoku_tools")
        self.game: Optional[SudokuGame] = None
        self.register(self.initialize_sudoku)
        self.register(self.get_current_grid)
        self.register(self.make_move)
        self.register(self.validate_solution)

    def initialize_sudoku(self, difficulty: str = "medium") -> str:
        puzzles = {
            "easy": [
                [5,3,0,0,7,0,0,0,0],
                [6,0,0,1,9,5,0,0,0],
                [0,9,8,0,0,0,0,6,0],
                [8,0,0,0,6,0,0,0,3],
                [4,0,0,8,0,3,0,0,1],
                [7,0,0,0,2,0,0,0,6],
                [0,6,0,0,0,0,2,8,0],
                [0,0,0,4,1,9,0,0,5],
                [0,0,0,0,8,0,0,7,9]
            ]
        }
        self.game = SudokuGame(puzzles.get(difficulty, "easy"))
        return f"New {difficulty} Sudoku game initialized"

    def get_current_grid(self) -> List[List[int]]:
        return self.game.solution if self.game else None

    def make_move(self, row: int, col: int, number: int) -> str:
        if not self.game:
            return "Game not initialized"
        success = self.game.update_cell(row, col, number)
        return "Valid move" if success else "Invalid move"

    def validate_solution(self) -> bool:
        return self.game.is_solved() if self.game else False

def print_grid(grid: List[List[int]]) -> None:
    print("\nCurrent Sudoku Grid:")
    for i, row in enumerate(grid):
        if i % 3 == 0 and i != 0:
            print("-"*23)
        row_str = " | ".join(
            " ".join(str(num) if num != 0 else "." for num in row[j:j+3]) 
            for j in range(0, 9, 3)
        )
        print(f"{' '.join(row_str)}")

sudoku_agent = Agent(
    model=DeepSeekChat(
        id="deepseek-chat",
        api_key="sk-",
        temperature=0.1
    ),
    tools=[SudokuTools()],
    description="Autonomous Sudoku solving agent with advanced reasoning capabilities",
    instructions=[
        "Analyze the Sudoku grid systematically row by row, column by column, and box by box",
        "Identify all possible candidates for each empty cell",
        "Apply logical deduction techniques: Naked Singles, Hidden Singles, etc.",
        "Choose moves with highest confidence first",
        "Explain reasoning in clear step-by-step format",
        "Validate each move before execution",
        "Continue until puzzle is completely solved"
    ],
    system_prompt="""You are an expert Sudoku solver. Your rules:
1. Use 0-based indexing for cell coordinates
2. Always check row, column, and 3x3 box constraints
3. Progressively eliminate possibilities through logical deduction
4. Format explanations with clear numbering and grid coordinates
5. Confirm solution validity at each step""",
    markdown=True,
    show_tool_calls=True
)

if __name__ == "__main__":
    # Initialize game
    print("Initializing Sudoku game...")
    initialization_response = sudoku_agent.run("Initialize easy Sudoku game")
    print(initialization_response.response)
    
    # Get initial grid state
    current_grid = sudoku_agent.tools[0].get_current_grid()
    print_grid(current_grid)
    
    # Solve the puzzle step-by-step
    step = 1
    max_steps = 50
    start_time = time.time()
    
    while not sudoku_agent.tools[0].validate_solution() and step <= max_steps:
        print(f"\n--- Step {step} ---")
        response = sudoku_agent.run(
            "Analyze current grid and make next logical move. "
            "Explain your reasoning in detail."
        )
        
        # Print results
        print(f"\nREASONING:\n{response.response}")
        print_grid(sudoku_agent.tools[0].get_current_grid())
        
        # Print performance metrics
        current_step = sudoku_agent.tools[0].game.steps[-1]
        print(f"Move Result: {current_step[3].upper()}")
        print(f"Time Taken: {time.time() - start_time:.2f}s")
        
        step += 1
        time.sleep(1)  # Rate limiting
    
    # Final status
    if sudoku_agent.tools[0].validate_solution():
        print("\nSUDOKU SOLVED SUCCESSFULLY!")
        print(f"Total Steps: {len(sudoku_agent.tools[0].game.steps)}")
        print(f"Total Time: {time.time() - start_time:.2f}s")
    else:
        print("\nSOLUTION ATTEMPT FAILED - MAX STEPS REACHED")