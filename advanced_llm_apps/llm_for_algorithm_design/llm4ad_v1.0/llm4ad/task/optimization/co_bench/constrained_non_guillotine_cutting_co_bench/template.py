template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(stock_length: int, stock_width: int, pieces: list) -> dict:
    """
    Solves the constrained non-guillotine cutting problem.
    Input kwargs:
      - stock_length (int): Length of the stock rectangle.
      - stock_width (int): Width of the stock rectangle.
      - pieces (list of dict): List of pieces, where each dict has:
            'length' (int), 'width' (int),
            'min' (int): minimum number required,
            'max' (int): maximum allowed,
            'value' (int): value of the piece.
    Evaluation Metric:
      The solution is scored as the sum of the values of all placed pieces,
      provided that every placement is valid (i.e., pieces lie within bounds,
      do not overlap, and the count for each type meets the specified [min, max] range).
      If any constraint is violated, the solution receives no score.
    Returns:
      A dictionary with one key:
          'placements': a list of placements, where each placement is a 4-tuple:
                        (piece_type, x, y, r)
                       - piece_type: 1-indexed index of the piece type.
                       - x, y: integer coordinates for the placement (bottom-left corner).
                       - r: rotation flag (0 for no rotation, 1 for 90° rotation).
    """
    # Placeholder implementation.
    # (A valid implementation would generate placements meeting all constraints.)
    return {'placements': []}
'''

task_description = ("The constrained non-guillotine cutting problem involves optimally arranging rectangular pieces "
                    "onto a single rectangular stock with fixed dimensions (stock_length and stock_width). Each piece "
                    "type has defined length, width, value, and minimum and maximum usage constraints. The "
                    "optimization goal is to maximize the total value of all placed pieces, subject to constraints "
                    "that each piece is entirely within stock boundaries, pieces do not overlap, each piece type’s "
                    "usage falls within its specified [min, max] range, and pieces may optionally be rotated by 90°. "
                    "The solution returns a set of placements indicating piece type, bottom-left coordinates (x, y), "
                    "and rotation status. If any constraint is violated, the solution receives no score."
                    "Help me design a novel algorithm to solve this problem.")
