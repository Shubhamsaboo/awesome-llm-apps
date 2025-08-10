template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(n: int, edges: list, adjacency: dict) -> dict:
    """
    Problem:
        Given a graph in DIMACS format (with vertices, edges, and an adjacency list),
        assign a positive integer color to each vertex (1..n) so that no two adjacent vertices
        share the same color. The objective is to use as few colors as possible.
    Input kwargs:
    The keyword arguments are expected to include at least:
      - n: int (int), the number of vertices.
      - edges: list of (u, v) tuples (tuple of int (int), int (int)) representing edges.
      - adjacency: dict mapping each vertex (1..n) (int) to a set of its adjacent vertices (set of int).
    Evaluation Metric:
        Let  k  be the number of distinct colors used.
        For every edge connecting two vertices with the same color, count one conflict ( C ).
        If  C > 0 , the solution is invalid and receives no score.
        Otherwise, the score is simply  k , with a lower  k  being better.
    Returns:
        A dictionary representing the solution, mapping each vertex_id (1..n) to a positive integer color.
    """
    ## placeholder.
    return {}  # Replace {} with the actual solution dictionary when implemented.
'''

task_description = ("Given a graph in DIMACS format with vertices, edges, and an adjacency list, the goal is to "
                    "assign a positive integer color (1..n) to each vertex while ensuring that no two adjacent "
                    "vertices share the same color. The objective is to minimize the number of distinct colors used. "
                    "If any two adjacent vertices have the same color, the solution is invalid and receives no score. "
                    "Otherwise, the score is equal to the number of distinct colors used, with a lower score being "
                    "better."
                    "Help me design a novel algorithm to solve this problem.")
