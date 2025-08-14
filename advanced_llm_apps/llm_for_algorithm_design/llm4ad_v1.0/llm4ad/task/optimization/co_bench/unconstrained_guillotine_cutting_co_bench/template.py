template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(m: int, stock_width: int, stock_height: int, pieces: dict, allow_rotation: bool = False) -> dict:
    """
    Solves the unconstrained guillotine cutting problem.
    Given a stock rectangle (with dimensions 'stock_width' and 'stock_height') and a set of pieces
    (provided as a dictionary 'pieces' mapping each piece_id to its specification {'l', 'w', 'value'}),
    the goal is to select and place some pieces (each used at most once) within the stock rectangle.
    If the keyword argument 'allow_rotation' is True, each piece may be placed in its original orientation or rotated 90° (swapping its dimensions);
    otherwise, pieces must be placed in their original orientation. In all cases, placements must not overlap and must lie entirely within the stock.
    Input kwargs:
        - m (int): Number of available pieces.
        - stock_width (int): The width of the stock rectangle.
        - stock_height (int): The height of the stock rectangle.
        - pieces (dict): A dictionary mapping piece_id (1-indexed) to a dict with keys:
              'l' (length), 'w' (width), and 'value' (value of the piece).
        - allow_rotation (bool): Indicates whether a piece is allowed to be rotated 90°.
    Evaluation metric:
        The performance is measured as the total value of the placed pieces (sum of individual values).
    Returns:
        A dictionary with a key "placements" whose value is a list.
        Each element in the list is a dictionary representing a placement with keys:
            - piece_id (int): Identifier of the placed piece.
            - x (int): x-coordinate of the bottom-left corner in the stock rectangle.
            - y (int): y-coordinate of the bottom-left corner in the stock rectangle.
            - orientation (int): 0 for original orientation; 1 if rotated 90° (only applicable if allow_rotation is True, otherwise default to 0).
    NOTE: This is a placeholder function. Replace the body with an actual algorithm if desired.
    """
    ## placeholder. You do not need to write anything here.
    return {"placements": []}
'''

task_description = ("The unconstrained guillotine cutting problem involves selecting and placing a subset of "
                    "available pieces within a fixed stock rectangle to maximize the total value of the placed "
                    "pieces. Each piece, defined by its length, width, and value, may be optionally rotated 90° if "
                    "allowed and used at most once. The challenge is to determine both the selection and the "
                    "positioning of these pieces such that they do not overlap and lie entirely within the stock’s "
                    "boundaries. This optimization problem formalizes the decision variables as the x and y "
                    "coordinates for the bottom-left placement of each piece and, if rotation is allowed, "
                    "a binary variable indicating its orientation, while the objective function is to maximize the "
                    "sum of the values of the pieces successfully placed within the stock."
                    "Help me design a novel algorithm to solve this problem.")
