template_program = '''
import numpy as np

def determine_next_assignment(remaining_items: List[int], remaining_capacities: List[int]) -> Tuple[int, Optional[int]]:
    """
    Determine the next item and bin to pack based on a greedy heuristic.

    Args:
        remaining_items: A list of remaining item weights.
        remaining_capacities: A list of remaining capacities of feasible bins.

    Returns:
        A tuple containing:
        - The selected item to pack.
        - The selected bin to pack the item into (or None if no feasible bin is found).
    """
    # Iterate through items in their original order
    for item in remaining_items:
        # Iterate through bins to find the first feasible one
        for bin_id, capacity in enumerate(remaining_capacities):
            if item <= capacity:
                return item, bin_id  # Return the selected item and bin
    return remaining_items[0], None  # If no feasible bin is found, return the first item and no bin
'''

task_description = '''
Given a set of bins and items, iteratively assign one item to feasible bins.
Design a constructive heuristic used in each iteration, with the objective of minimizing the used bins.
'''
