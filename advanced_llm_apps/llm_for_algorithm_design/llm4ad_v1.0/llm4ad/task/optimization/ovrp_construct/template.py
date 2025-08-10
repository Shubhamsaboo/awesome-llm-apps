template_program = '''
import numpy as np

def select_next_node(current_node: int, depot: int, unvisited_nodes: np.ndarray, rest_capacity: np.ndarray, demands: np.ndarray, distance_matrix: np.ndarray) -> int:
    """Design a novel algorithm to select the next node in each step.
    Args:
        current_node: ID of the current node.
        depot: ID of the depot.
        unvisited_nodes: Array of IDs of unvisited nodes.
        rest_capacity: rest capacity of vehicle
        demands: demands of nodes
        distance_matrix: Distance matrix of nodes.
    Return:
        ID of the next node to visit.
    """
    next_node = unvisited_nodes[0]
    return next_node
'''

task_description = """
Given a set of customers and a fleet of vehicles with limited capacity,
the task is to design a novel algorithm to select the next node in each step,
with the objective of minimizing the total cost.
"""
