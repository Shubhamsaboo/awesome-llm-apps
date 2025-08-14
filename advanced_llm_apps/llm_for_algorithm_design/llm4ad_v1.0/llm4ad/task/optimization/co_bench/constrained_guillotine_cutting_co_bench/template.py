template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(m: int, stock_length: int, stock_width: int, piece_types: list) -> dict:
    """
    Solves the Fixed Orientation Guillotine Cutting problem.
    Problem Description:
      Given a rectangular stock sheet (with specified length and width) and a set of piece types
      (each defined by a length, width, an upper bound on the number of times it may appear, and a value),
      the goal is to determine a placement for the pieces such that:
        - Each placed piece lies entirely within the stock sheet.
        - Pieces do not overlap.
        - The number of pieces placed for any type does not exceed its allowed maximum.
        - The orientation of the pieces is fixed (i.e. no rotation is allowed).
        - The total value reported equals the sum of the values of the placed pieces.
    Input kwargs (for one case):
      - m: integer, the number of piece types.
      - stock_length: integer, the length of the stock sheet.
      - stock_width: integer, the width of the stock sheet.
      - piece_types: list of dictionaries. Each dictionary has the keys:
            'length' : int, the length of the piece.
            'width'  : int, the width of the piece.
            'max'    : int, maximum number of pieces allowed.
            'value'  : int, value of the piece.
    Returns:
      A dictionary with the following keys:
        - total_value: int, the computed total value (must equal the sum of the piece values in placements).
        - placements: list of placements, where each placement is a tuple of 6 integers:
              (piece_type_index, x, y, placed_length, placed_width, orientation_flag)
          The orientation_flag is always 0 since rotation is not allowed.
    """
    # Your optimization/placement algorithm should go here.
    # For now, this is a placeholder that meets the output format requirements.

    # Example placeholder output (no actual pieces placed):
    return {"total_value": 0, "placements": []}
'''

task_description = ("The problem involves optimizing the guillotine feasible placement of a set of rectangular pieces "
                    "on a given stock sheet to maximize total value. Each piece type is characterized by its length, "
                    "width, an upper bound on the number of times it may appear in the final cutting pattern, "
                    "and an assigned value. Orientation of the pieces is fixed (the edges of the pieces are parallel "
                    "to the edges of the sheet). The task is to select and place pieces such that each lies "
                    "completely within the boundaries of the stock sheet, no two pieces overlap, and the number of "
                    "pieces of any type does not exceed its specified maximum. A set of placements is considered "
                    "guillotine feasible if there exists at least one straight cut (vertical or horizontal) that does "
                    "not slice through any rectangle, and the property holds recursively on the resulting subregions. "
                    "Empty regions or regions exactly matching a placed piece are considered valid.The objective is "
                    "to maximize the sum of the values of the placed pieces; however, if any spatial or count "
                    "constraint is violated, the solution is deemed invalid. The output is defined as a dictionary "
                    "reporting the total value and a list of placements, with each placement specified by the piece "
                    "type index, x and y coordinates, placed dimensions, and orientation flag."
                    "Help me design a novel algorithm to solve this problem.")
