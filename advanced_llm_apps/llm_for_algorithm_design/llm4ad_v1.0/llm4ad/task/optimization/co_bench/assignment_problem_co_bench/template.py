template_program = '''
import numpy as np
from scipy.optimize import linear_sum_assignment
def solve(num_items: int, cost_matrix: np.ndarray) -> dict:
    """
    Solves an instance of the Assignment Problem.
    Given n items and an n×n cost matrix (where cost_matrix[i][j] is the cost of assigning
    item (i+1) to agent (j+1)), the goal is to determine a permutation (a one-to-one assignment
    between items and agents) that minimizes the total cost. The returned solution is a
    dictionary with:
      - "total_cost": The sum of the costs of the chosen assignments.
      - "assignment": A list of n tuples (i, j), where i is the item number (1-indexed)
                      and j is the assigned agent number (1-indexed).
    Input kwargs:
      - n: int, the number of items/agents.
      - cost_matrix: numpy.ndarray, a 2D array with shape (n, n) containing the costs.
    Returns:
      A dictionary with keys "total_cost" and "assignment" representing the optimal solution.
    """
    # Your algorithm implementation goes here.
    # For example, you may use the Hungarian algorithm.
    return {"total_cost": None, "assignment": None}
'''

task_description = ("The Assignment Problem involves optimally assigning  n  items to  n  agents based on a provided  "
                    "n \\times n  cost matrix, where each entry \( \\text{cost\matrix}[i][j] \) denotes the cost of "
                    "assigning item  i+1  to agent  j+1 . The goal is to identify a permutation—each item assigned "
                    "exactly one agent—that minimizes the total assignment cost. Formally, this is an optimization "
                    "problem to find a permutation \pi of agents such that the total cost \sum{i=1}^{n} \\text{"
                    "cost\_matrix}[i-1][\pi(i)-1] is minimized. The solution returned includes both the minimal total "
                    "cost and the corresponding optimal assignments."
                    "Help me design a novel algorithm to solve this problem.")
