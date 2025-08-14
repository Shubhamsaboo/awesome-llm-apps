template_program = '''
import numpy as np

def select_next_item(remaining_capacity: int, remaining_items: List[Tuple[int, int, int]]) -> Tuple[int, int, int] | None:
    """
    Select the item with the highest value-to-weight ratio that fits in the remaining capacity.

    Args:
        remaining_capacity: The remaining capacity of the knapsack.
        remaining_items: List of tuples containing (weight, value, index) of remaining items.

    Returns:
        The selected item as a tuple (weight, value, index), or None if no item fits.
    """
    best_item = None
    best_ratio = -1  # Initialize with a negative value to ensure any item will have a higher ratio

    for item in remaining_items:
        weight, value, index = item
        if weight <= remaining_capacity:
            ratio = value / weight  # Calculate value-to-weight ratio
            if ratio > best_ratio:
                best_ratio = ratio
                best_item = item

    return best_item
'''

task_description = '''
Given a set of items with weights and values, the goal is to select a subset of items
that maximizes the total value while not exceeding the knapsack's capacity.
Help me design a novel algorithm to select the next item in each step.
'''
