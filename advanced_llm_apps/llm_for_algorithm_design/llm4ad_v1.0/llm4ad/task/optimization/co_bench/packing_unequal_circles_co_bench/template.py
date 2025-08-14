template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(n: int, cx: float, cy: float, R: float, radii: list) -> dict:
    """
    Solve the unequal circle packing problem for the maximize-number case.
    Problem Description:
      Given a circular container with center (cx, cy) and radius R, and n circles with specified radii (sorted in increasing order),
      the task is to select and pack a prefix of the sorted list—i.e., if circle i is packed, then all circles with a smaller index must also be packed—in order to maximize the number of circles placed.
      Each packed circle must be fully contained within the container, meaning that the distance from its center to (cx, cy) plus its radius must not exceed R, and no two packed circles may overlap, which requires that the distance between any two centers is at least the sum of their respective radii.
    Input kwargs:
      - n     : int, the number of circles.
      - cx    : float, x-coordinate of the container's center.
      - cy    : float, y-coordinate of the container's center.
      - R     : float, the radius of the container.
      - radii : list of float, the radius of each circle (assumed sorted in increasing order).
    Returns:
      A dictionary with one key:
        - "coords": a list of n (x, y) tuples corresponding to the centers of the circles.
          For circles that are not packed, the coordinates default to (-1, -1).
    """
    return {"coords": []}
'''

task_description = ("The problem involves packing a subset of unequal circles into a fixed circular container with "
                    "radius R_0 and center at the origin, where each circle i has a given radius R_i (sorted in "
                    "non-decreasing order) and is associated with a binary decision variable \\alpha_i indicating "
                    "whether it is packed. The goal is to maximize the number of circles packed—that is, "
                    "maximize \sum_{i=1}^{n}\\alpha_i—subject to two sets of nonlinear constraints: (1) each packed "
                    "circle must lie entirely within the container, which is enforced by ensuring that the distance "
                    "from its center to the container’s center plus its radius does not exceed R_0; and (2) any two "
                    "packed circles must not overlap, meaning the distance between their centers must be at least the "
                    "sum of their radii."
                    "Help me design a novel algorithm to solve this problem.")
