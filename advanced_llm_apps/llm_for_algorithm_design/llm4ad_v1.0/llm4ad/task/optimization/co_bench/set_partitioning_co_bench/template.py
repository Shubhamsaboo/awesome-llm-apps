template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(num_rows: int, num_columns: int, columns_info: dict) -> dict:
    """
    Solve a set partitioning problem instance.
    The problem: Given a set of rows and a set of columns (each with an associated cost and a set
    of rows it covers), select a subset of columns so that each row is covered exactly once and the
    total cost is minimized.
    Input kwargs:
  - num_rows (int): Total number of rows. (int)
  - num_columns (int): Total number of columns. (int)
  - columns_info (dict): Dictionary mapping 1-indexed column indices (int) to a tuple:
                         (cost (int), set of row indices (set[int]) covered by that column).
    Evaluation metric:
      The objective score equals the sum of the costs of the selected columns if the solution is feasible,
      i.e., if every row is covered exactly once. Otherwise, the solution is invalid and receives no score.
    Returns:
      A dictionary with key "selected_columns" containing a list of chosen column indices in strictly increasing order.
      (This is a placeholder implementation.)
    """
    # Placeholder implementation.
    # You must replace the following line with your actual solution logic.
    return {"selected_columns": []}
'''

task_description = ("This problem involves solving a set partitioning instance where the goal is to choose a subset "
                    "of columns such that each row is covered exactly once while minimizing the total cost. Each "
                    "column is associated with a cost and covers a specific set of rows. The optimization problem is "
                    "defined by selecting columns from a given set so that every row is covered precisely once, "
                    "and the sum of the selected columns’ costs is minimized. If the solution fails to cover every "
                    "row exactly once, then no score is awarded."
                    "Help me design a novel algorithm to solve this problem.")
