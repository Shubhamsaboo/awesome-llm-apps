template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(container: tuple, n: int, cargo_vol: float, box_types: list) -> dict:
    """
    Solves the Container Loading with Weight Restrictions problem.
    Input kwargs (for one test case):
      - container (tuple of int): (L, W, H) representing the container dimensions in cm.
      - n (int): the number of box types.
      - cargo_vol (float): the total cargo volume in m³ (provided for consistency).
      - box_types (list of dict): one per box type. Each dictionary has the keys:
            'length' (int), 'length_flag' (int),
            'width' (int),  'width_flag' (int),
            'height' (int), 'height_flag' (int),
            'count' (int),  'weight' (float),
            'lb1' (float), 'lb2' (float), 'lb3' (float).
    The problem is to select and place boxes (each possibly in one of three allowed orientations)
    inside the container so as to maximize the ratio of the total volume of placed boxes (each based on its original dimensions)
    to the container’s volume, while obeying placement, support, and load–bearing constraints.
    Evaluation metric:
      The score is the container volume utilization (i.e. total placed boxes volume divided by container volume)
      if the solution is valid according to all constraints; otherwise the score is 0.0.
    Placeholder implementation: No boxes are placed.
    Returns a dictionary with keys:
      - 'instance': instance number (int),
      - 'util': achieved utilization (float),
      - 'm': number of placements (int),
      - 'placements': a list of placements; each placement is a dict with keys:
            'box_type' (int, 1-indexed), 'orientation' (int: 1, 2, or 3),
            'x', 'y', 'z' (floats for the lower–left–front corner in cm).
    """
    # Placeholder: return an empty solution.
    return {
        'instance': 1,
        'util': 0.0,
        'm': 0,
        'placements': []
    }
'''

task_description = ("The Container Loading with Weight Restrictions problem aims to maximize the utilization of a "
                    "container’s volume by selecting and strategically placing boxes inside it. Given a container "
                    "with specified dimensions (length, width, height) and multiple types of boxes, "
                    "each characterized by their dimensions, quantities, weights, and load-bearing constraints, "
                    "the optimization goal is to determine the placement and orientation of these boxes (with each "
                    "box allowed three possible orientations) that maximizes the ratio of total occupied box volume "
                    "to container volume. The solution must strictly adhere to spatial constraints (boxes must fit "
                    "entirely within the container without overlapping), load-bearing constraints (boxes must support "
                    "the weight of boxes stacked above them according to given limits), and orientation restrictions. "
                    "The optimization quality is evaluated by the achieved utilization metric, defined as the total "
                    "volume of successfully placed boxes divided by the container volume; if any constraint is "
                    "violated, the utilization score is zero."
                    "Help me design a novel algorithm to solve this problem.")
