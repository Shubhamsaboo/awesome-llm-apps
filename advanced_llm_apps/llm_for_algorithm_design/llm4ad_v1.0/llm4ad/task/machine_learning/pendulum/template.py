template_program = '''
import numpy as np

def choose_action(x: float, y: float, av: float, last_action: float) -> float:
    """
    Args:
        x: cos(theta), between [-1, 1]
        y: sin(theta), between [-1, 1]
        av: angular velocity of the pendulum, between [-8.0, 8.0]
        last_action: the last torque applied to the pendulum, a float between [-2.0, 2.0]

    Return:
         A float representing the torque to be applied to the pendulum.
         The value should be in the range of [-2.0, 2.0].
    """
    action = np.random.uniform(-2.0, 2.0)
    return action
'''

task_description = ("Implement a novel control strategy for the inverted pendulum swing-up problem. The goal is to "
                    "apply an appropriate torque at each step to swing the pendulum into an upright position (center "
                    "of gravity directly above the fixed point) and stabilize it. The torque should be selected based "
                    "on the pendulum's current state, including its x-y coordinates (`cos(theta)` and `sin(theta)`) "
                    "and angular velocity. The solution should minimize the time required to reach the upright "
                    "position while ensuring stability.")
