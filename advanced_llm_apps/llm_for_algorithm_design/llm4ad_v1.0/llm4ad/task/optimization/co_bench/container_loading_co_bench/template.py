template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(problem_index: int, container: tuple, box_types: dict) -> dict:
    """
    Solves a container loading problem.
    Input kwargs:
      - problem_index: an integer identifier for the test case.
      - container: a tuple of three integers (container_length, container_width, container_height).
      - box_types: a dictionary mapping each box type (integer) to a dict with:
            'dims': a list of three integers [d1, d2, d3],
            'flags': a list of three binary integers [f1, f2, f3] indicating if that dimension can be vertical,
            'count': an integer number of available boxes of that type.
    Evaluation Metric:
      The solution is evaluated by computing the volume utilization ratio, which is the sum of the volumes
      of all placed boxes divided by the container volume. Placements must be valid (i.e. respect orientation,
      remain within the container, and not overlap). If any placement is invalid, the score is 0.0.
    Return:
      A dictionary with key 'placements', whose value is a list of placement dictionaries.
      Each placement dictionary must contain 7 integers with the following keys/values:
          box_type, container_id, x, y, z, v, hswap
      where 'v' is the index (0, 1, or 2) for the vertical dimension and 'hswap' is a binary flag (0 or 1)
      indicating whether the horizontal dimensions are swapped.
    """
    # Placeholder implementation.
    return {'placements': []}
'''

task_description = ("Solves a container loading problem: Given a 3D container of specified dimensions and multiple "
                    "box types—each defined by dimensions, orientation constraints, and available quantity—the goal "
                    "is to optimally place these boxes within the container to maximize the volume utilization ratio. "
                    "Each box placement must respect orientation constraints (vertical alignment flags), fit entirely "
                    "within container boundaries, and avoid overlaps. The solution returns precise coordinates and "
                    "orientations for each box placement, quantified by a volume utilization score calculated as the "
                    "total volume of placed boxes divided by the container volume. Invalid placements result in a "
                    "score of 0.0."
                    "Help me design a novel algorithm to solve this problem.")
