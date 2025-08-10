template_program = '''
import numpy as np

def equation(strain: np.ndarray, temp: np.ndarray, params: np.ndarray) -> np.ndarray:
    """ Mathematical function for stress in Aluminium rod
    Args:
        strain: A numpy array representing observations of strain.
        temp: A numpy array representing observations of temperature.
        params: Array of numeric constants or parameters to be optimized

    Return:
        A numpy array representing stress as the result of applying the mathematical function to the inputs.
    """
    return params[0] * strain  +  params[1] * temp
'''

task_description = ("Find the mathematical function skeleton that represents stress, given data on strain and "
                    "temperature in an Aluminium rod for both elastic and plastic regions.")

