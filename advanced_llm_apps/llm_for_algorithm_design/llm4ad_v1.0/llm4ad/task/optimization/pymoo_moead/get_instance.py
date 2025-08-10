# Module Name: get_instance
# Last Revision: 2025/07/14
# Description: Generates DTLZ4 problem instances for MOEAD evaluation.
#              This module is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
import pickle

import numpy as np

from pymoo.problems import get_problem

# class GetData:
#     def __init__(self, n_var, n_obj):
#         """
#         Initialize parameters for the WFG problem.
#         Args:
#             n_var (int): The number of decision variables.
#             n_obj (int): The number of objectives.
#         """
#         # For WFG problems, ensure the number of decision variables is sufficient
#         k = 2 * (n_obj - 1)
#         if n_var < k + 1:
#             raise ValueError(f"For WFG1 with {n_obj} objectives, n_var must be at least {k + 1}")
#
#         self.n_var = n_var
#         self.n_obj = n_obj
#
#     def get_problem_instance(self):
#         """
#         Generate and return a WFG1 problem instance using the pymoo library.
#         This is a more complex benchmark problem than DTLZ.
#         """
#         # WFG problems typically require a position parameter k; a standard configuration is used here.
#         k = 2 * (self.n_obj - 1)
#         return get_problem("wfg1", n_var=self.n_var, n_obj=self.n_obj, k=k)

class GetData:
    def __init__(self, n_var, n_obj):
        """
        Initialize parameters for the DTLZ problem.
        Args:
            n_var (int): The number of decision variables.
            n_obj (int): The number of objectives.
        """
        self.n_var = n_var
        self.n_obj = n_obj

    def get_problem_instance(self):
        """
        Generate and return a DTLZ4 problem instance using the pymoo library.
        """
        return get_problem("DTLZ4", n_var=self.n_var, n_obj=self.n_obj)


if __name__ == '__main__':
    # Demonstrate the use of the GetData class
    print("--- Demonstrating GetData Class ---")
    gd = GetData(n_var=10, n_obj=3)
    dtlz4_problem = gd.get_problem_instance()
    print("Successfully created a DTLZ4 problem instance:")
    print(dtlz4_problem)
    print("\n")

    # Provide a code template for a Large Language Model (LLM) to implement a custom decomposition function
    prompt_code_temp = '''import numpy as np

def custom_decomposition(F: np.ndarray,
                         weights: np.ndarray,
                         ideal_point: np.ndarray,
                         **kwargs) -> np.ndarray:
    """Design a novel decomposition method for MOEA/D.

    Args:
        F (np.ndarray): A set of objective vectors for the population.
        weights (np.ndarray): The weight vectors for the subproblems.
        ideal_point (np.ndarray): The ideal point found so far.

    Returns:
        np.ndarray: The aggregated scalar value for each solution.
    """
    # Example: Tchebycheff decomposition
    # This is a placeholder and should be replaced by a novel algorithm.
    v = np.abs(F - ideal_point) * weights
    return np.max(v, axis=1)
'''

    print("--- Template for LLM-designed Decomposition Function ---")
    print(prompt_code_temp)
