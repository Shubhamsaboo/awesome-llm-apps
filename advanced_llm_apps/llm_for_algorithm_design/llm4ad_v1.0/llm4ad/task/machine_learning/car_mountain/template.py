template_program = '''
import numpy as np

def choose_action(pos: float, v: float, last_action: int) -> int:
    """Return the action for the car to proceed the next move.
    Args:
        pos: Car's position, a float ranges between [-1.2, 0.6].
        v: Car's velocity, a float ranges between [-0.07, 0.07].
        last_action: Car's next move, a int ranges between [0, 1, 2].
    Return:
         An integer representing the selected action for the car.
         0: accelerate to left
         1: don't accelerate
         2: accelerate to right
    """
    return np.random.randint(3)
'''

task_description = ("Implement a function that designing a novel strategy function that guide the car along an uneven "
                    "road, moving step by step towards a target. At each step, a specific action will be chosen based "
                    "on the car's current position and velocity, aiming to reach the destination in the minimum "
                    "number of steps.")
