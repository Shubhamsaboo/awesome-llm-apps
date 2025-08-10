template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(nudes: list) -> dict:
    """
    Solve a TSP instance.
    Args:
        - nodes (list): List of (x, y) coordinates representing cities in the TSP problem
                     Format: [(x1, y1), (x2, y2), ..., (xn, yn)]
    Returns:
        dict: Solution information with:
            - 'tour' (list): List of node indices representing the solution path
                            Format: [0, 3, 1, ...] where numbers are indices into the nodes list
    """

    return {
        'tour': [],
    }
'''

task_description = ("The Traveling Salesman Problem (TSP) is a classic combinatorial optimization problem where, "
                    "given a set of cities with known pairwise distances, the objective is to find the shortest "
                    "possible tour that visits each city exactly once and returns to the starting city. More "
                    "formally, given a complete graph G = (V, E) with vertices V representing cities and edges E with "
                    "weights representing distances, we seek to find a Hamiltonian cycle (a closed path visiting each "
                    "vertex exactly once) of minimum total weight."
                    "Help me design a novel algorithm to solve this problem.")
