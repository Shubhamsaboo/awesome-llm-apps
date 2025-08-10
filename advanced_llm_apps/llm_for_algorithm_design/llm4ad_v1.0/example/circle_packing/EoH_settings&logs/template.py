template_program = '''
import numpy as np
import math
def pack_circles(n: int) -> np.ndarray:
    """
    Pack n circles in a unit square to maximize sum of radii.
    
    Args:
        n: Number of circles to pack

    Returns:
        Numpy array of shape (n, 3) where each row is (x, y, radius)
        All values should be between 0 and 1
        Circles must not overlap
        
    Important: Set "all" random seeds to 2025, including the packages (such as scipy sub-packages) involving random seeds.
    """

    grid_size = int(np.ceil(np.sqrt(n)))
    radius = 0.5 / grid_size

    circles = []
    for i in range(n):
        row = i // grid_size
        col = i % grid_size
        x = (col + 0.5) / grid_size
        y = (row + 0.5) / grid_size
        circles.append([x, y, radius])

    return np.array(circles)
'''

task_description = "Implement a function that uses a constructive heuristic to pack n non-overlapping circles iteratively within a unit square to maximize the sum of their radii"