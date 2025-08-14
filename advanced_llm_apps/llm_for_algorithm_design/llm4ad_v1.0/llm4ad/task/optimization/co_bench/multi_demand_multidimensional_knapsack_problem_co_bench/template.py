template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(n:int, m:int, q:int, A_leq:list, b_leq:list, A_geq:list, b_geq:list, cost_vector:list, cost_type:str) -> dict:
    """
    Solve a given MDMKP test instance.
    Input (via kwargs):
      - n: int
          Number of decision variables.
      - m: int
          Number of <= constraints.
      - q: int
          Number of active >= constraints (subset of the full set).
      - A_leq: list of lists of int
          Coefficient matrix for <= constraints (dimensions: m x n).
      - b_leq: list of int
          Right-hand side for <= constraints (length m).
      - A_geq: list of lists of int
          Coefficient matrix for >= constraints (dimensions: q x n).
      - b_geq: list of int
          Right-hand side for >= constraints (length q).
      - cost_vector: list of int
          Objective function coefficients (length n).
      - cost_type: str
          Type of cost coefficients ("positive" or "mixed").
    Output:
      A dictionary with the following keys:
        - 'optimal_value': int/float
             The optimal objective function value (if found).
        - 'x': list of int
             Binary vector (0 or 1) representing the decision variable assignment.
    TODO: Implement the actual solution algorithm for the MDMKP instance.
    """
    # TODO: Define your model variables, constraints, and objective function.
    # For example, you might use an integer programming solver (e.g., PuLP, Gurobi, or another solver)
    # to model and solve the instance.

    # Placeholder solution:
    solution = {
        'optimal_value': None,  # Replace with the computed objective value.
        'x': [0] * kwargs.get('n', 0),  # Replace with the computed decision vector.
    }
    return solution
'''

task_description = ("The Multi-Demand Multidimensional Knapsack Problem (MDMKP) is a binary optimization problem that "
                    "extends the classical MKP by incorporating both upper-bound (≤) and lower-bound (≥) constraints. "
                    "Formally, given n decision variables x_j \in \{0,1\}, the goal is to maximize \sum_{j=1}^n c_j "
                    "x_j subject to \sum_{j=1}^n a_{ij} x_j \le b_i for i=1,\dots,m and \sum_{j=1}^n a_{ij} x_j \ge "
                    "b_i for i=m+1,\dots,m+q. Instances are generated from standard MKP problems by varying the "
                    "number of ≥ constraints (with q taking values 1, m/2, or m) and by using two types of cost "
                    "coefficients (positive and mixed), thereby producing six distinct variants per base instance. "
                    "This formulation enables rigorous evaluation of algorithms in contexts where both resource "
                    "limits and demand fulfillment must be simultaneously addressed."
                    "Help me design a novel algorithm to solve this problem.")
