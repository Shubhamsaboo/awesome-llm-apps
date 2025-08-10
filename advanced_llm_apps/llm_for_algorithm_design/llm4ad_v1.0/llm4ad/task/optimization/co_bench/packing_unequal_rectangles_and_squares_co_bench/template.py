template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(n: int, cx: float, cy: float, R: float, items: list, shape: str, rotation: bool) -> dict:
    """
    Solves the "maximum number" packing problem for unequal rectangles and squares
    in a fixed-size circular container.
    Input kwargs:
      - n         : int, total number of available items (rectangles or squares)
      - cx, cy    : floats, coordinates of the container center (typically the origin)
      - R         : float, radius of the circular container
      - items     : list of tuples, where each tuple (L, W) specifies the dimensions
                    of an item (for a square, L == W). Items are assumed to be ordered
                    by increasing size.
      - shape     : str, either "rectangle" or "square"
      - rotation  : bool, indicating whether 90° rotation is allowed
    Objective:
      The goal is to pack as many items as possible inside the container. An item is
      considered packed if its entire geometry lies completely within the circular
      container and it does not overlap any other packed item.
    Evaluation:
      A valid solution is one in which no packed item extends outside the container
      and no two packed items overlap. The quality of a solution is measured solely by
      the number of items successfully packed (i.e. the higher the number, the better).
    Returns:
      A dictionary with the key 'placements' containing a list of exactly n tuples.
      Each tuple is of the form (x-coordinate, y-coordinate, theta) where:
          - (x-coordinate, y-coordinate) is the center position of the item,
          - theta is the rotation angle in degrees (counter-clockwise from the horizontal) 90 or 0.
          - For any item that is not packed, set its x and y coordinates to -1
            (and theta can be set to 0).
    Note:
      This is a placeholder header. The actual solution logic is not implemented here.
    """
    ## placeholder.
    return {'placements': []}
'''

task_description = ("We are given a set of n unequal rectangles (or squares), each with specified dimensions, "
                    "and a fixed circular container of radius R centered at the origin. The problem is to decide "
                    "which rectangles to pack and where to position them—by choosing binary selection variables and "
                    "continuous center coordinates—so that every packed rectangle is entirely contained within the "
                    "circle and no two packed rectangles overlap. For each rectangle, the four corners must lie "
                    "inside the circle, and if an item is not packed it is forced to a dummy position. The objective "
                    "is to maximize the number of packed items, i.e., maximize \sum_{i=1}^{n} alpha_i (or a related "
                    "sum when each alpha_i is binary). Note that the rotation of the rectagular (by 90 degrees) is "
                    "sometimes allowed and your algorithm should take that into account."
                    "Help me design a novel algorithm to solve this problem.")
