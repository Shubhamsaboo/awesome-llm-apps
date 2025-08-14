template_program = '''
import numpy as np
def determine_next_assignment(remaining_items: List[Tuple[int, int]], point_matrices: List[List[List[int]]]) -> Tuple[Tuple[int, int], int]:
    """
    A simple heuristic function to select the next item and bin for packing.

    Args:
        remaining_items: A list of tuples, where each tuple represents the (width, height) of an item.
        point_matrices: A list of 2D matrices representing the occupied (1) and unoccupied (0) points in each bin.

    Returns:
        A tuple containing:
        - The selected item (width, height).
        - The selected bin index (or None if no bin is feasible).
    """
    # Select the largest item (based on area) from the remaining items
    selected_item = max(remaining_items, key=lambda item: item[0] * item[1])

    # Try to find a feasible bin for the selected item
    for bin_idx, point_matrix in enumerate(point_matrices):
        bin_width = len(point_matrix)
        bin_height = len(point_matrix[0]) if bin_width > 0 else 0
        # Check if the item fits in the bin
        if bin_width >= selected_item[0] and bin_height >= selected_item[1]:
            # Check for a feasible position in the bin
            for x in range(bin_width - selected_item[0] + 1):
                for y in range(bin_height - selected_item[1] + 1):
                    # Check if the area is unoccupied
                    if all(point_matrix[x + dx][y + dy] == 0 for dx in range(selected_item[0]) for dy in range(selected_item[1])):
                        return selected_item, bin_idx
    # If no feasible bin is found, return None for the bin
    return selected_item, None

'''

task_description = '''
Given a set of rectangular bins and rectangular items, iteratively assign each item to a feasible position in one of the bins. Design a constructive heuristic that, in each iteration, selects the best item and placement from the remaining items and feasible corners, with the objective of minimizing the number of used bins.
'''
