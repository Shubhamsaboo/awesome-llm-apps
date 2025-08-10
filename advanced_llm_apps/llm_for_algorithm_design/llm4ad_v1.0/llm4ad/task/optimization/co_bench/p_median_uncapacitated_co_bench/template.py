template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(n: int, m: int, p: int, dist: list) -> dict:
    """
    Solves the uncapacitated p-median problem on a given graph.
    Input kwargs:
        - n: int, number of vertices.
        - m: int, number of edges.
        - p: int, number of medians to choose.
        - dist: list of lists, the complete cost matrix (n x n) computed via Floyd’s algorithm.
    Evaluation metric:
        The total assignment cost, defined as the sum (over all vertices) of the shortest distance
        from that vertex to its closest chosen median.
    Returns:
        A dictionary with a single key:
            - 'medians': a list of exactly p distinct integers (each between 1 and n) representing
              the indices of the chosen medians.
    Note: This is a placeholder. The actual solution logic should populate the 'medians' list.
    """
    # Placeholder implementation; replace with your solution logic.
    return {"medians": []}
'''

task_description = ("The uncapacitated p-median problem is a combinatorial optimization problem defined on a given "
                    "graph  G = (V, E)  with  n  vertices and  m  edges. The objective is to select  p  medians ("
                    "facility locations) from the set of vertices such that the total assignment cost is minimized. "
                    "The assignment cost is computed as the sum of the shortest distances from each vertex to its "
                    "nearest selected median, where distances are given by a precomputed complete cost matrix ("
                    "obtained via Floyd’s algorithm). Formally, given the cost matrix  D \in \mathbb{R}^{n \times n} "
                    ", the optimization problem seeks to find a subset  S \subseteq V  with  |S| = p  that minimizes "
                    "the function: \sum_{v \in V} \min_{s \in S} D(v, s) where  D(v, s)  is the shortest-path "
                    "distance between vertex  v  and median  s . The solution consists of a list of exactly  p  "
                    "distinct vertices representing the chosen medians."
                    "Help me design a novel algorithm to solve this problem.")
