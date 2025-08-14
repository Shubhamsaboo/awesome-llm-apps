template_program = '''
def select_next_node(current_node: int, depot: int, unvisited_nodes: np.ndarray, rest_capacity: np.ndarray, current_time: np.ndarray,\
                        demands: np.ndarray, distance_matrix: np.ndarray, time_windows: np.ndarray) -> int:
    """Design a novel algorithm to select the next node in each step.
    Args:
        current_node: ID of the current node.
        depot: ID of the depot.
        unvisited_nodes: Array of IDs of unvisited nodes.
        rest_capacity: Rest capacity of vehicle
        current_time: Current time
        demands: Demands of nodes
        distance_matrix: Distance matrix of nodes.
        time_windows: Time windows of nodes.
    Return:
        ID of the next node to visit.
    """
    next_node = unvisited_nodes[0]
    return next_node
'''

task_description = "The task involves finding optimal routes for a fleet of vehicles to serve a set of customers, respecting time windows and vehicle capacity constraints. Help me design an algorithm to select the next node in each step."
