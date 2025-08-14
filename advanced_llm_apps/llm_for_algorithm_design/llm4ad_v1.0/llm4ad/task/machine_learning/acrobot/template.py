template_program = '''
import numpy as np

def choose_action(ct1: float, st1: float, ct2: float, st2: float, avt1: float, avt2: float, last_action: int) -> int: 
    """
    Design a novel algorithm to select the action in each step.

    Args:
        ct1: cosine of theta1, float between [-1, 1].
        st1: sine of theta1, float between [-1, 1]
        ct2: cosine of theta2, float between [-1, 1].
        st2: sine of theta2, float between [-1, 1].
        avt1: angular velocity of theta1, float between [-12.567, 12.567].
        avt2: angular velocity of theta2, float between [-28.274, 28.274].


    Return:
         An integer representing the selected action for the acrobot.
         0: apply -1 torque on actuated  joint.
         1: apply 0 torque on actuated joint
         2: apply +1 torque on actuated joint.

    """
    # this is a placehold, replace it with your algorithm
    action =  np.random.randint(3)

    return action
'''

task_description = ("I need help designing an innovative heuristic strategy function to control an acrobot, aiming to "
                    "swing the lower link to generate enough momentum for the upper link to reach a target height. At "
                    "each step, the function should select a specific action based on the acrobot's joint angles and "
                    "angular velocities to efficiently reach the goal without unnecessary oscillations or excessive "
                    "control effort.")
