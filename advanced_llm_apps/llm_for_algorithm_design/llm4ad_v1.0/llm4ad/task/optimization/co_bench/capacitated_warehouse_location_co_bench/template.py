template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(m: int, n: int, warehouses: list, customers: list) -> dict:
    """
    Solves the Capacitated Warehouse Location Problem with Splittable Customer Demand.
    Input kwargs:
  - m (int): Number of potential warehouses
  - n (int): Number of customers
  - warehouses (list of dict): A list of dictionaries, each with keys 'capacity' (float) and 'fixed_cost' (float)
  - customers (list of dict): A list of dictionaries, each with keys 'demand' (float) and 'costs' (list of float) representing the per-unit assignment cost from each warehouse
    Evaluation Metric:
      The objective is to minimize the total cost, computed as:
         (Sum of fixed costs for all open warehouses)
       + (Sum of per-unit assignment costs for each unit of demand allocated from warehouses to customers)
      For each customer, the sum of allocations from all warehouses must equal the customer's demand.
      For each warehouse, the total allocated demand across all customers must not exceed its capacity.
      If a solution violates any of these constraints, the solution is considered infeasible and no score is provided.
    Returns:
      A dictionary with the following keys:
         'total_cost': (float) The computed objective value (cost) if the solution is feasible;
                         otherwise, no score is provided.
         'warehouse_open': (list of int) A list of m integers (0 or 1) indicating whether each warehouse is closed or open.
         'assignments': (list of list of float) A 2D list (n x m) where each entry represents the amount of customer i's demand supplied by warehouse j.
    """
    ## placeholder. You do not need to write anything here.
    return {
        "total_cost": 0.0,
        "warehouse_open": [0] * kwargs["m"],
        "assignments": [[0.0] * kwargs["m"] for _ in range(kwargs["n"])]
    }
'''

task_description = ("The Capacitated Warehouse Location Problem with Splittable Demand aims to determine which "
                    "warehouses to open and how to allocate portions of customer demands among these warehouses in "
                    "order to minimize total costs. Given a set of potential warehouse locations, each with a fixed "
                    "opening cost and capacity limit, and a set of customers with individual demands and associated "
                    "per-unit assignment costs to each warehouse, the objective is to decide which warehouses to open "
                    "and how to distribute each customer's demand among these open warehouses. The allocation must "
                    "satisfy the constraint that the sum of portions assigned to each customer equals their total "
                    "demand, and that the total demand allocated to any warehouse does not exceed its capacity. The "
                    "optimization seeks to minimize the sum of fixed warehouse opening costs and the total per-unit "
                    "assignment costs. However, if any solution violates these constraints (i.e., a customer’s demand "
                    "is not fully satisfied or a warehouse’s capacity is exceeded), then no score is provided."
                    "Help me design a novel algorithm to solve this problem.")
