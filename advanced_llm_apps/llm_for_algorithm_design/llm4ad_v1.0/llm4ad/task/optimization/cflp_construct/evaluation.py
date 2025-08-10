# Module Name: CFLPEvaluation
# Last Revision: 2025/2/16
# Description: Evaluates the Capacitated Facility Location Problem (CFLP).
#              Given a set of facilities and customers, the goal is to assign customers to facilities
#              while respecting facility capacities and minimizing total costs.
#              This module is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Parameters:
#    - timeout_seconds: Maximum allowed time (in seconds) for the evaluation process: int (default: 60).
#    - n_instance: Number of problem instances to generate: int (default: 16).
#    - n_facilities: Number of facilities: int (default: 5).
#    - n_customers: Number of customers: int (default: 8).
#    - max_capacity: Maximum capacity of each facility: int (default: 100).
#    - max_demand: Maximum demand of each customer: int (default: 20).
#    - max_cost: Maximum cost of assigning a customer to a facility: int (default: 50).
# 
# References:
#   - Fei Liu, Rui Zhang, Zhuoliang Xie, Rui Sun, Kai Li, Xi Lin, Zhenkun Wang, 
#       Zhichao Lu, and Qingfu Zhang, "LLM4AD: A Platform for Algorithm Design 
#       with Large Language Model," arXiv preprint arXiv:2412.17287 (2024).
#
# ------------------------------- Copyright --------------------------------
# Copyright (c) 2025 Optima Group.
# 
# Permission is granted to use the LLM4AD platform for research purposes. 
# All publications, software, or other works that utilize this platform 
# or any part of its codebase must acknowledge the use of "LLM4AD" and 
# cite the following reference:
# 
# Fei Liu, Rui Zhang, Zhuoliang Xie, Rui Sun, Kai Li, Xi Lin, Zhenkun Wang, 
# Zhichao Lu, and Qingfu Zhang, "LLM4AD: A Platform for Algorithm Design 
# with Large Language Model," arXiv preprint arXiv:2412.17287 (2024).
# 
# For inquiries regarding commercial use or licensing, please contact 
# http://www.llm4ad.com/contact.html
# --------------------------------------------------------------------------


from __future__ import annotations
from typing import Callable, Any, List, Tuple
import numpy as np
import matplotlib.pyplot as plt

from llm4ad.base import Evaluation
from llm4ad.task.optimization.cflp_construct.get_instance import GetData
from llm4ad.task.optimization.cflp_construct.template import template_program, task_description

__all__ = ['CFLPEvaluation']


class CFLPEvaluation(Evaluation):
    """Evaluator for the Capacitated Facility Location Problem."""

    def __init__(self,
                 timeout_seconds: int = 60,
                 n_instance: int = 16,
                 n_facilities: int = 50,
                 n_customers: int = 50,
                 max_capacity: int = 100,
                 max_demand: int = 20,
                 max_cost: int = 50,
                 **kwargs):
        """
        Initialize the evaluator.
        """
        super().__init__(
            template_program=template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds
        )

        self.n_instance = n_instance
        self.n_facilities = n_facilities
        self.n_customers = n_customers
        self.max_capacity = max_capacity
        self.max_demand = max_demand
        self.max_cost = max_cost
        getData = GetData(self.n_instance, self.n_facilities, self.n_customers, self.max_capacity, self.max_demand, self.max_cost)
        self._datasets = getData.generate_instances()

    def evaluate_program(self, program_str: str, callable_func: Callable) -> Any | None:
        return self.evaluate_cflp(callable_func)

    def plot_solution(self, facility_capacities: List[int], customer_demands: List[int], assignments: List[List[int]], assignment_costs: List[List[int]]):
        """
        Plot the final solution of assignments for the Capacitated Facility Location Problem.

        Args:
            facility_capacities: A list of facility capacities.
            customer_demands: A list of customer demands.
            assignments: A list of assignments, where each assignment is a list of customer indices assigned to a facility.
            assignment_costs: A 2D list (matrix) of costs, where the cost of assigning customer j to facility i is assignment_costs[i][j].
        """
        n_facilities = len(facility_capacities)
        n_customers = len(customer_demands)

        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot facilities and customers
        for facility in range(n_facilities):
            # Plot facility as a rectangle
            ax.add_patch(plt.Rectangle((facility - 0.4, -0.4), 0.8, 0.8, color='skyblue', label='Facility' if facility == 0 else None))
            ax.text(facility, 0, f'F{facility}\nCap: {facility_capacities[facility]}', ha='center', va='center', fontsize=10)

            # Plot assigned customers
            for customer in assignments[facility]:
                ax.plot([facility, customer], [0, 1], 'k--', linewidth=0.5)  # Line connecting facility to customer
                ax.add_patch(plt.Circle((customer, 1), 0.1, color='orange', label='Customer' if facility == 0 and customer == 0 else None))
                ax.text(customer, 1.1, f'C{customer}\nDem: {customer_demands[customer]}', ha='center', va='bottom', fontsize=8)
                # Add cost as text near the line
                ax.text((facility + customer) / 2, 0.5, f'Cost: {assignment_costs[facility][customer]}', ha='center', va='center', fontsize=8, rotation=45)

        # Set axis limits and labels
        ax.set_xlim(-1, n_customers)
        ax.set_ylim(-0.5, 1.5)
        ax.set_xticks(range(n_customers))
        ax.set_yticks([0, 1])
        ax.set_yticklabels(['Facilities', 'Customers'])
        ax.set_title('Capacitated Facility Location Problem - Assignments')
        ax.legend(loc='upper right')

        # Show the plot
        plt.tight_layout()
        plt.show()

    def assign_customers(self, facility_capacities: List[int], customer_demands: List[int], assignment_costs: List[List[int]], eva: Callable) -> Tuple[int, List[List[int]]]:
        """
        Assign customers to facilities using a constructive heuristic.

        Args:
            facility_capacities: A list of facility capacities.
            customer_demands: A list of customer demands.
            assignment_costs: A 2D list (matrix) of costs, where the cost of assigning customer j to facility i is assignment_costs[i][j].
            eva: The constructive heuristic function to select the next customer-facility assignment.

        Returns:
            A tuple containing:
            - The total cost of the assignments.
            - A list of assignments, where each assignment is a list of customer indices assigned to a facility.
        """
        n_facilities = len(facility_capacities)
        n_customers = len(customer_demands)
        assignments = [[] for _ in range(n_facilities)]  # Initialize empty assignments for each facility
        remaining_customers = list(range(n_customers))  # List of remaining customer indices
        remaining_capacities = facility_capacities.copy()  # Copy of facility capacities to track remaining capacities
        total_cost = 0  # Total cost of assignments

        while remaining_customers:
            # Use the heuristic to select the next customer-facility assignment
            selected_customer, selected_facility = eva(assignments, remaining_customers, remaining_capacities, customer_demands, assignment_costs)

            if selected_facility is not None:
                # Assign the selected customer to the selected facility
                assignments[selected_facility].append(selected_customer)
                # Update the remaining capacity of the selected facility
                remaining_capacities[selected_facility] -= customer_demands[selected_customer]
                # Add the assignment cost to the total cost
                total_cost += assignment_costs[selected_facility][selected_customer]
            else:
                # If no feasible assignment is found, stop assigning (no more feasible assignments)
                break

            # Remove the selected customer from the remaining customers
            remaining_customers.remove(selected_customer)

        return total_cost, assignments

    def evaluate_cflp(self, eva: Callable) -> float:
        """
        Evaluate the constructive heuristic for the Capacitated Facility Location Problem.

        Args:
            instance_data: List of dictionaries containing facility capacities, customer demands, and assignment costs.
            n_ins: Number of instances to evaluate.
            eva: The constructive heuristic function to evaluate.

        Returns:
            The average total cost across all instances.
        """
        total_cost = 0

        for instance in self._datasets[:self.n_instance]:
            facility_capacities = instance["facility_capacities"]
            customer_demands = instance["customer_demands"]
            assignment_costs = instance["assignment_costs"]
            cost, _ = self.assign_customers(facility_capacities, customer_demands, assignment_costs, eva)
            total_cost += cost

        average_cost = total_cost / self.n_instance
        return -average_cost


if __name__ == '__main__':

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


    bp1d = CFLPEvaluation()
    ave_bins = bp1d.evaluate_program('_', select_next_assignment)
    print(ave_bins)
