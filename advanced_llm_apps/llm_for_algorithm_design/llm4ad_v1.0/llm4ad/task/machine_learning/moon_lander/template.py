template_program = '''
import numpy as np
def choose_action(xc: float, yc: float, xv: float, yv: float, a: float, av: float, lc: float, rc: float, last_action: int) -> int:
    """
    Args:
        xc: x coordinate, between [-1, 1]
        yc: y coordinate, between [-1, 1]
        xv: x velocity
        yv: y velocity
        a: angle
        av: angular velocity
        lc: 1 if first leg has contact, else 0
        rc: 1 if second leg has contact, else 0.
        last_action: Lander's last move, a int ranges in [0, 1, 2, 3].

    Return:
         An integer representing the selected action for the lander.
         0: do nothing
         1: fire left orientation engine
         2: upward
         3: fire right orientation engine
    """
    action = np.random.randint(4)
    return action
'''

task_description = ("Implement a novel heuristic strategy heuristic strategy function that guides the "
                    "lander to achieve a safe landing at the center of the land, step-by-step. At each step, "
                    "a specific action will be selected based on the lander's current state, with the goal of "
                    "landing on the target location in the minimum possible steps. A 'safe landing' is "
                    "defined as a touchdown with minimal vertical velocity, upright orientation, "
                    "and both angular velocity and angle at zero.")
