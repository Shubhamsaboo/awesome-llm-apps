template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(n:int, cx: float, cy: float, R: float, radii: list) -> dict:
    """
    Solve the Unequal Circle Packing problem (Maximize Area version).
    Problem Description:
      Given a circular container with center (cx, cy) and radius R, and n circles
      with specified radii (provided in 'radii'), decide which circles to pack and
      determine the centers (x_i, y_i) for the packed circles such that:
      1. Containment: Each packed circle i must lie completely within the container.
         (x_i - cx)^2 + (y_i - cy)^2 <= α_i * (R - radii[i])^2,  for i = 1,...,n.
         (If α_i = 0, then the circle is not packed and its center is set to (cx, cy).)
      2. Non-Overlap: For every pair of circles i and j (with i < j), if both are packed,
         their centers must satisfy:
         (x_i - x_j)^2 + (y_i - y_j)^2 >= ( (α_i + α_j - 1) * (radii[i] + radii[j]) )^2.
         (This is a linearized version of the product α_i * α_j used in the paper.)
      3. Binary decisions: α_i ∈ {0, 1} for i = 1,...,n, where α_i = 1 indicates circle i is packed.
         (For circles not packed, we force (x_i, y_i) to equal (cx, cy).)
      4. Objective: Maximize the total area of the circles packed:
         maximize sum_{i=1}^n α_i * (pi * radii[i]^2).
    Input kwargs:
      - n     : int, the number of circles.
      - cx    : float, x-coordinate of the container's center.
      - cy    : float, y-coordinate of the container's center.
      - R     : float, the radius of the container.
      - radii : list of float, each element is the radius of a circle.
    Returns:
      A dictionary with one key:
        - "coords": a list of n (x, y) tuples corresponding to the centers of the circles.
                    For circles not packed (α_i = 0), (x, y) should be (-1, -1).
    """
    # ===== Placeholder Implementation =====

    return {"coords": []}
'''

task_description = ("The problem involves packing a subset of unequal circles into a fixed circular container with "
                    "radius R_0 and center at the origin, where each circle i has a given radius R_i (sorted in "
                    "non-decreasing order) and is associated with a binary decision variable \\alpha_i indicating "
                    "whether it is packed. The goal is to maximize the total area of all circles packed—that is, "
                    "maximize \sum_{i=1}^{n}\\alpha_i*pi*R_i^2—subject to two sets of nonlinear constraints: (1) each "
                    "packed circle must lie entirely within the container, which is enforced by ensuring that the "
                    "distance from its center to the container’s center plus its radius does not exceed R_0; and (2) "
                    "any two packed circles must not overlap, meaning the distance between their centers must be at "
                    "least the sum of their radii."
                    "Help me design a novel algorithm to solve this problem.")
