template_program = '''
import numpy as np

def select_next_assignment(current_assignment: List[int], flow_matrix: np.ndarray, distance_matrix: np.ndarray) -> List[int]:
    """
    A heuristic for the Quadratic Assignment Problem.

    Args:
        current_assignment: Current assignment of facilities to locations (-1 means unassigned).
        flow_matrix: Flow matrix between facilities.
        distance_matrix: Distance matrix between locations.

    Returns:
        Updated assignment of facilities to locations.
    """
    n_facilities = len(current_assignment)
    
    # Find the first unassigned facility and the first available location
    for facility in range(n_facilities):
        if current_assignment[facility] == -1:
            # Find the first available location
            for location in range(n_facilities):
                if location not in current_assignment:
                    current_assignment[facility] = location
                    break
            break
    
    return current_assignment
'''

task_description = '''
The task is to assign a set of facilities to a set of locations in such a way that the total cost of interactions between facilities is minimized.
Help me design a novel algorithm to select the next operation in each step.
'''
