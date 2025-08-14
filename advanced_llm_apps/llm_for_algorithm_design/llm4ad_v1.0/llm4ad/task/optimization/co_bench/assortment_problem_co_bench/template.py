template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(m: int, stocks: list, pieces: list) -> dict:
    """
    Solves the rectangular piece arrangement optimization problem to minimize the overall waste area percentage.
    Given:
      - m (int): Number of piece types.
      - stocks (list of dict): Each dict represents a stock type with keys:
            'length' (float), 'width' (float), 'fixed_cost' (float).
      - pieces (list of dict): Each dict represents a piece type with keys:
            'length' (float), 'width' (float), 'min' (int), 'max' (int), 'value' (float).
    Objective:
      Arrange rectangular pieces (which may be rotated by 90°) into stock rectangles such that the overall waste area percentage is minimized.
      The waste area percentage is computed as:
             Waste Percentage = (Total Stock Area - Total Used Area) / (Total Stock Area)
    Constraints:
      • Each piece must lie entirely within its assigned stock rectangle.
      • Pieces must not overlap within the same stock rectangle.
      • The number of pieces placed for each piece type must lie within its specified minimum and maximum bounds.
      • You may use unlimited many instances of each selected stock type, but the solution can include at most 2 distinct stock types.
    Output:
      Returns a dictionary with two keys (exactly follow this format):
        - "objective": The overall waste area percentage (float) as computed by the evaluation function.
        - "placements": A dictionary mapping stock instance ids (1-indexed) to their placement details.
          Each stock instance is represented by a dictionary with the following keys:
              'stock_type': (the 1-indexed id of the stock type used for this instance),
              'placements': a list of placements for pieces within that stock instance.
                  Each placement is a dict with keys:
                      'piece'       (piece type, 1-indexed, 1 <= piece type <= m),
                      'x'           (x-coordinate of the bottom-left corner),
                      'y'           (y-coordinate of the bottom-left corner),
                      'orientation' (0 for normal, 1 for rotated 90°).
    NOTE: The returned data should adhere to the output format required for evaluation.
    """
    # ----- INSERT YOUR SOLUTION ALGORITHM HERE -----
    # For demonstration purposes, we provide a dummy solution that does not place any pieces.
    # In a real solution, you would compute placements that respect all constraints.

    # Dummy solution: Create a single stock instance of the first stock type, with no pieces placed.
    solution = {
        "objective": 0.0,  # With no placements, the evaluation function would compute a waste area percentage of 0.0.
        "placements": {
            1: {
                "stock_type": 1,
                "placements": []
            }
        }
    }
    return solution
'''

task_description = ("This optimization problem involves arranging a set of rectangular pieces within available stock "
                    "rectangles to minimize the overall waste area percentage. Each stock rectangle has a defined "
                    "area, and each piece—which may be rotated by 90°—must be fully contained within a stock without "
                    "overlapping with other pieces. Additionally, each piece type has specific total minimum and "
                    "maximum placement limits. You have access to an unlimited number of stocks for each type, "
                    "but you may use at most two stock types. The objective is to achieve the lowest possible waste "
                    "area percentage, defined as the ratio of unused area to the total stock area. Solutions must "
                    "ensure efficient resource utilization while satisfying all geometric and quantity constraints. "
                    "Any violation of these constraints results in no score."
                    "Help me design a novel algorithm to solve this problem.")
