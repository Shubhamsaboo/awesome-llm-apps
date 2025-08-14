task_description = """
You are tasked with designing a key component for a Multi-Objective Evolutionary Algorithm based on Decomposition (MOEA/D).
Your objective is to create a novel decomposition strategy that effectively transforms the multi-objective DTLZ1 problem
into a series of single-objective subproblems. The performance of your strategy will be measured by the hypervolume (HV)
of the resulting Pareto front; a higher HV indicates a better set of solutions.
"""

template_program = '''
import numpy as np

def custom_decomposition(F: np.ndarray,
                         weights: np.ndarray,
                         ideal_point: np.ndarray,
                         **kwargs) -> np.ndarray:
    """Design a novel decomposition method for MOEA/D.

    Args:
        F (np.ndarray): A set of objective vectors for the population.
                        Shape: (n_solutions, n_objectives)
        weights (np.ndarray): The weight vectors for the subproblems.
                              Shape: (n_solutions, n_objectives)
        ideal_point (np.ndarray): The ideal point found so far.
                                  Shape: (n_objectives,)

    Returns:
        np.ndarray: The aggregated scalar value for each solution.
                    Shape: (n_solutions,)
    """
    # Default implementation: Tchebycheff decomposition.
    # Replace this with your novel algorithm.
    v = np.abs(F - ideal_point) * weights
    return np.max(v, axis=1)
'''

