template_program = '''
import numpy as np

def equation(x: float, params: np.ndarray) -> float:
    """ A ODE mathematical function    
    Args:
        x: the initial float value of the ode formula
        params: a 1-d Array of numeric constants or parameters to be optimized

    Return:
        A numpy array representing the result of applying the mathematical function to the inputs.
    """
    y = params[0] * x + params[2]
    return y
'''

task_description = ("Find the ODE mathematical function skeleton, given data on initial x. The function should be differentiable, continuous."
                    "Only selectable components: "
                    "1. Basic operators: +, -, *, /, ^, np.sqrt, np.exp, np.log, np.abs"
                    "2. Trigonometric expressions: np.sin, np.cos, np.tan, np.arcsin, np.arccos, np.arctan"
                    "3. Standard constants: 'np.pi' represents pi and 'np.e' represents Euler's number")
