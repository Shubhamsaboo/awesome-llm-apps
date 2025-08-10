template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(best_known: float, n: int, p: int, Q: float, customers: list) -> dict:
    """
    Solve the Capacitated P-Median Problem.
    This function receives the data for one problem instance via keyword arguments:
      - best_known (float): Best known solution value for reference.
      - n (int): Number of customers.
      - p (int): Number of medians to choose.
      - Q (float): Capacity limit for each median.
      - customers (list of tuples): Each tuple is (customer_id, x, y, demand).
    The goal is to select p medians (from the customers) and assign every customer to one
    of these medians so that the total cost is minimized. The cost for a customer is the
    Euclidean distance (rounded down to the nearest integer) to its assigned median, and the
    total demand assigned to each median must not exceed Q.
    Evaluation Metric:
      The solution is evaluated by computing the ratio:
          score = best_known / computed_total_cost,
      where computed_total_cost is the sum over all customers of the (floored) Euclidean distance
      to its assigned median.
    Note: This is a placeholder function. Replace the placeholder with an actual algorithm.
    Returns:
      A dictionary with the following keys:
        - 'objective': (numeric) the total cost (objective value) computed by the algorithm.
        - 'medians': (list of int) exactly p customer IDs chosen as medians.
        - 'assignments': (list of int) a list of n integers, where the i-th integer is the customer
                         ID (from the chosen medians) assigned to customer i.
    """
    # Placeholder: Replace this with your actual implementation.
    # For now, we return an empty solution structure.
    return {
        "objective": 0,  # total cost (to be computed)
        "medians": [],  # list of p medians (customer IDs)
        "assignments": []  # list of n assignments (each is one of the medians)
    }
'''

task_description = ("The Capacitated P-Median Problem is a facility location optimization problem where the objective "
                    "is to select exactly  p  customers as medians (facility locations) and assign each customer to "
                    "one of these medians to minimize the total cost, defined as the sum of the Euclidean distances ("
                    "rounded down to the nearest integer) between customers and their assigned medians. Each median "
                    "has a capacity constraint  Q , meaning the total demand of the customers assigned to it cannot "
                    "exceed  Q . A feasible solution must respect this capacity constraint for all medians; "
                    "otherwise, it receives a score of zero. The solution is evaluated by the ratio \\text{score} = "
                    "\\frac{\\text{best\_known}}{\\text{computed\_total\_cost}} , where computed_total_cost is the total "
                    "assignment cost if all constraints are satisfied; otherwise, the score is zero. The output "
                    "consists of the total cost (if feasible), the selected medians, and the customer assignments."
                    "Help me design a novel algorithm to solve this problem.")
