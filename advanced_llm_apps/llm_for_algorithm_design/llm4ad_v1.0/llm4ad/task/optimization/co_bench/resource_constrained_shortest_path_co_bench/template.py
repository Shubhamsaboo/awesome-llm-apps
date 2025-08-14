template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(n:int, m:int, K:int, lower_bounds:list, upper_bounds:list, vertex_resources:list, graph:dict) -> dict:
    """
    Solve the Resource Constrained Shortest Path problem.
    Input kwargs should include:
      - n (int): number of vertices,
      - m (int): number of arcs,
      - K (int): number of resources,
      - lower_bounds (list of float): list of lower limits for each resource,
      - upper_bounds (list of float): list of upper limits for each resource,
      - vertex_resources (list of list of float): list (of length n) of lists (of length K) with the resource consumption at each vertex,
      - graph (dict): dictionary mapping each vertex (1-indexed) to a list of arcs, where each arc is a tuple
                      (end_vertex (int), cost (float), [arc resource consumptions] (list of float)).
    Evaluation Metric:
      If the computed path is valid (i.e. it starts at vertex 1, ends at vertex n, every transition is
      defined in the graph, and the total resource consumption from both vertices and arcs is within the
      specified bounds for each resource), then the score equals the total arc cost along the path.
      Otherwise, the solution is invalid and receives no score.
    Returns:
      A dictionary with keys:
         "total_cost": total cost (a float) of the computed path,
         "path": a list of vertex indices (integers) defining the path.
    (Placeholder implementation)
    """
    # Placeholder implementation.
    n = kwargs.get("n", 1)
    # Return a trivial solution: just go directly from vertex 1 to vertex n.
    return {"total_cost": 0.0, "path": [1, n]}
'''

task_description = ("This problem involves finding the shortest path from vertex 1 to vertex n in a directed graph "
                    "while satisfying resource constraints. Specifically, each vertex and arc has associated resource "
                    "consumptions, and the cumulative consumption for each resource must fall within the provided "
                    "lower_bounds and upper_bounds. The input includes the number of vertices (n), arcs (m), "
                    "resource types (K), resource consumption at each vertex, and a graph represented as a mapping "
                    "from vertices to lists of arcs (each arc being a tuple of end vertex, cost, and arc resource "
                    "consumptions). The optimization objective is to minimize the total arc cost of the path, "
                    "with the condition that the path is valid—meaning it starts at vertex 1, ends at vertex n, "
                    "follows defined transitions in the graph, and respects all resource bounds; if any of these "
                    "constraints are not met, the solution receives no score."
                    "Help me design a novel algorithm to solve this problem.")
