template_program = '''
import numpy as np
import networkx as nx
def solve(graph: networkx.Graph):
    """
    Solve the Maximum Independent Set problem for a given test case.
   Input:
        kwargs (dict): A dictionary with the following keys:
            - graph (networkx.Graph): The graph to solve
    Returns:
        dict: A solution dictionary containing:
            - mis_nodes (list): List of node indices in the maximum independent set
    """
    # TODO: Implement your MIS solving algorithm here. Below is a placeholder.
    solution = {
        'mis_nodes': [0, 1, ...],
    }
    return solution
'''

task_description = ("The Maximum Independent Set (MIS) problem is a fundamental NP-hard optimization problem in graph "
                    "theory. Given an undirected graph G = (V, E), where V is a set of vertices and E is a set of "
                    "edges, the goal is to find the largest subset S ⊆ V such that no two vertices in S are adjacent "
                    "(i.e., connected by an edge)."
                    "Help me design a novel algorithm to solve this problem.")
