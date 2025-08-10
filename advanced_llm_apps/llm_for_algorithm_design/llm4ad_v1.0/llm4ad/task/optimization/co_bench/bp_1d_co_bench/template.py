template_program = '''
import numpy as np
from scipy.optimize import linear_sum_assignment
def solve(id: str, bin_capacity: int, num_items: int, items: list[int], **kwargs) -> dict:
    """
    Solve the one-dimensional bin packing problem for a single test case.
    Input kwargs (for a single test case):
      - id:           The problem identifier (string)
      - bin_capacity: The capacity of each bin (int)
      - num_items:    The number of items (int)
      - items:        A list of item sizes (list of ints)
      - **kwargs:     Other unused keyword arguments
    Evaluation metric:
      - The solution is scored by the total number of bins used.
      - If the solution is invalid (e.g., items are missing or duplicated, or bin capacity is exceeded),
        a penalty of 1,000,000 is added.
    Returns:
      A dictionary with:
        - 'num_bins': An integer, the number of bins used.
        - 'bins': A list of lists, where each inner list contains the 1-based indices of items assigned to that bin.
    Note: This is a placeholder implementation.
    """
    # Placeholder: Replace with your bin packing solution.
    return {
        'num_bins': 0,
        'bins': []
    }
'''

task_description = ("The **one-dimensional bin packing problem** seeks to minimize the number of bins required to "
                    "pack a given set of items while ensuring that the sum of item sizes within each bin does not "
                    "exceed the specified bin capacity. Given a test case with an identifier (`id`), "
                    "a fixed `bin_capacity`, and a list of `num_items` with their respective sizes (`items`), "
                    "the objective is to find a packing arrangement that uses the least number of bins. The solution "
                    "is evaluated based on the total `num_bins` used, with invalid solutions (e.g., missing or "
                    "duplicated items, or bins exceeding capacity) incurring a inf heavy penalty. The output must "
                    "include the number of bins used and a valid assignment of item indices to bins."
                    "Help me design a novel algorithm to solve this problem.")
