template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(points: list) -> dict:
    """
    Solves a single instance of the Euclidean Steiner Problem.
    Problem Description:
      Given a set of 2D points (terminals), the goal is to compute additional Steiner points
      such that when you compute the MST over the union of the original terminals and these Steiner points,
      the total length (measured via Euclidean distances) is minimized.
      (Recall, the Euclidean distance between two points (x1, y1) and (x2, y2) is sqrt((x1-x2)^2 + (y1-y2)^2).)
    Input kwargs:
      - points: a list of points, where each point is a tuple of floats (x, y),
                representing the coordinates of an original terminal.
    Returns:
      A dictionary with one key:
         - "steiner_points": a list of (x, y) tuples representing the additional Steiner points.
      It is assumed that the candidate solution’s computed total length can be derived by computing
      the MST over the union of the original terminals and the returned Steiner points.
    """
    points = kwargs.get("points")
    if points is None:
        raise ValueError("Missing input: 'points' key is required.")

    # Placeholder for an actual Steiner tree algorithm:
    # In a real implementation, you would compute extra Steiner points to lower the MST length.
    steiner_points = []  # For now, return no additional Steiner points.

    return {"steiner_points": steiner_points}
'''

task_description = ("Given a set of 2D points (terminals), the goal of the Euclidean Steiner Problem is to compute a "
                    "tree connecting all terminals with minimum total length. The total length is measured as the sum "
                    "of Euclidean distances (where the Euclidean distance between two points (x1,y1) and (x2,"
                    "y2) is sqrt((x1-x2)² + (y1-y2)²)). Unlike a Minimum Spanning Tree (MST) computed solely on the "
                    "given terminals, a Steiner tree may introduce extra points, called Steiner points, to reduce the "
                    "overall length. In this formulation, it is assumed that the final candidate tree’s total length "
                    "is given by the MST computed on the union of the original terminals and the reported Steiner "
                    "points. A lower ratio (candidate_tree_length/MST_original_length) indicates a better solution."
                    "Help me design a novel algorithm to solve this problem.")
