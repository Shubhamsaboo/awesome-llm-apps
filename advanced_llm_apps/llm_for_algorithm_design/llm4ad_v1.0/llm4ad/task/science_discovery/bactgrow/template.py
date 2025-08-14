template_program = '''
import numpy as np

def equation(b: np.ndarray, s: np.ndarray, temp: np.ndarray, pH: np.ndarray, params: np.ndarray) -> np.ndarray:
    """ Mathematical function for bacterial growth rate
    Args:
        b: A numpy array representing observations of population density of the bacterial species.
        s: A numpy array representing observations of substrate concentration.
        temp: A numpy array representing observations of temperature.
        pH: A numpy array representing observations of pH level.
        params: Array of numeric constants or parameters to be optimized

    Return:
        A numpy array representing bacterial growth rate as the result of applying the mathematical function to the inputs.
    """
    return params[0] * b + params[1] * s + params[2] * temp + params[3] * pH + params[4]
'''

task_description = ("Find the mathematical function skeleton that represents E. Coli bacterial growth rate, "
                    "given data on population density, substrate concentration, temperature, and pH level.")
