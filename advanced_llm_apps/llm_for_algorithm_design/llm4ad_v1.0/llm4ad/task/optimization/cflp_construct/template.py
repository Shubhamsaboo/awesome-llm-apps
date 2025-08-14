template_program = '''
import numpy as np

def select_next_assignment(assignments: List[List[int]], remaining_customers: List[int], remaining_capacities: List[int], customer_demands: List[int], assignment_costs: List[List[int]]) -> Tuple[int, int]:
    """
    Constructive heuristic for the Capacitated Facility Location Problem.
    Assigns the next customer to the facility with the lowest cost that has sufficient capacity.

    Args:
        assignments: Current assignments of customers to facilities.
        remaining_customers: List of customer indices not yet assigned.
        remaining_capacities: Remaining capacities of facilities.
        customer_demands: List of customer demands.
        assignment_costs: 2D list of assignment costs (facility-to-customer).

    Returns:
        A tuple containing:
        - The selected customer index.
        - The selected facility index (or None if no feasible assignment exists).
    """
    # Iterate over all remaining customers
    for customer in remaining_customers:
        # Iterate over all facilities to find the one with the lowest cost and sufficient capacity
        min_cost = float('inf')
        selected_facility = None

        for facility in range(len(remaining_capacities)):
            if remaining_capacities[facility] >= customer_demands[customer] and assignment_costs[facility][customer] < min_cost:
                min_cost = assignment_costs[facility][customer]
                selected_facility = facility

        # If a feasible facility is found, return the customer and facility
        if selected_facility is not None:
            return customer, selected_facility

    # If no feasible assignment is found, return None
    return None, None
'''

task_description = '''
Given facilities with capacities and customers, iteratively assign customers to facilities while respecting capacity constraints and minimizing total costs. Design a novel algorithm to select the next assignment in each step.
'''
