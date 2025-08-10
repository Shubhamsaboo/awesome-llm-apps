template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(n: int, cx: float, cy: float, R: float, items: list, shape: str, rotation: bool) -> dict:
    """
    Solves the problem of packing a subset of unequal rectangles and squares into a fixed‐size circular container
    with the objective of maximizing the total area of the items placed inside the container.
    Input kwargs:
      - n         : int, the number of items (rectangles or squares)
      - cx, cy    : floats, the coordinates of the container center
      - R         : float, the radius of the container
      - items     : list of tuples, where each tuple (L, W) gives the dimensions of an item
                    (for a square, L == W)
      - shape     : string, either "rectangle" or "square"
      - rotation  : bool, whether 90° rotation is allowed (True or False)
    Objective:
      - Select and place a subset of the given items so that each packed item lies completely inside the circular container,
        no two packed items overlap, and the sum of the areas of the packed items is maximized.
      - An item that is not packed contributes zero area.
    Returns:
      A dictionary with the key 'placements' containing a list of exactly n tuples.
      Each tuple is (x-coordinate, y-coordinate, theta) where:
          - (x-coordinate, y-coordinate) is the center position of the item (if packed),
          - theta is the rotation angle in degrees (counter-clockwise from the horizontal). 90 or 0.
          - For an unpacked item, x and y should be set to -1 and theta to 0 (or another default value).
    Note: This is a placeholder. The actual solution logic is not implemented here.
    """
    ## placeholder.
    return {'placements': []}
'''

task_description = ("We consider the problem of selecting and placing a subset of  n  unequal rectangles (or squares) "
                    "into a fixed‐size circular container of radius  R  so as to maximize the total area of the "
                    "packed items. Each item  i  has given dimensions  L_i  and  W_i  (with  L_i = W_i  for squares) "
                    "and an associated area  L_iW_i . The decision variables include a binary indicator \\alpha_i for "
                    "whether item  i  is packed and continuous variables (x_i, y_i) for the placement of its center, "
                    "along with a rotation angle  \\theta_i  when 90^\circ rotations are allowed. The formulation "
                    "enforces that for every packed item, all four of its rotated corners must lie within the circle, "
                    "and that no two packed items overlap; if an item is not packed, it is fixed at a dummy position."
                    "Help me design a novel algorithm to solve this problem.")
