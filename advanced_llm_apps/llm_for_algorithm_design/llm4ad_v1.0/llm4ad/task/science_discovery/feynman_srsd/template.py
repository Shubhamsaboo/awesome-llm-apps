template_program = '''
import numpy as np

def equation(xs: np.ndarray, params: np.ndarray) -> np.ndarray:
    """ Mathematical function
    Args:
        xs: A 2-d numpy array.
        params: Array of numeric constants or parameters to be optimized.

    Return:
        A numpy array.
    """
    return params[0] * x[0] + params[1] * x[0] + params[2]
'''

task_description = "Find the mathematical function skeleton to fit a dataset, you don't have to use all the params."
