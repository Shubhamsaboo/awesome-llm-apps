# Module Name: QAPEvaluation
# Last Revision: 2025/2/16
# Description: Evaluates the Quadratic Assignment Problem (QAP).
#       The QAP involves assigning a set of facilities to a set of locations in such a way that the total cost of interactions between facilities is minimized.
#       This module is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Parameters:
#   - timeout_seconds: Maximum allowed time (in seconds) for the evaluation process: int (default: 20).
#   - n_facilities: Number of facilities to assign: int (default: 50).
#   - n_instance: Number of problem instances to generate: int (default: 10).
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
import numpy as np
from typing import Callable, Any, List, Tuple
import matplotlib.pyplot as plt

from llm4ad.base import Evaluation
from llm4ad.task.optimization.qap_construct.get_instance import GetData
from llm4ad.task.optimization.qap_construct.template import template_program, task_description

__all__ = ['QAPEvaluation']


class QAPEvaluation(Evaluation):
    """Evaluator for the Quadratic Assignment Problem."""

    def __init__(self,
                 timeout_seconds=20,
                 n_facilities=50,
                 n_instance=16,
                 **kwargs):
        """
        Initializes the QAP evaluator.
        """
        super().__init__(
            template_program=template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds
        )

        self.n_instance = n_instance
        self.n_facilities = n_facilities
        self.data_generator = GetData(self.n_instance, self.n_facilities)
        self._datasets = self.data_generator.generate_instances()

    def evaluate_program(self, program_str: str, callable_func: Callable) -> Any | None:
        """
        Evaluates the program (constructive heuristic) for the QAP.

        Args:
            program_str: Program string (not used here, but kept for compatibility).
            callable_func: The constructive heuristic function to evaluate.

        Returns:
            The average total cost across all instances.
        """
        return self.evaluate_qap(callable_func)

    def plot_solution(self, flow_matrix: np.ndarray, distance_matrix: np.ndarray, assignment: List[int]):
        """
        Plot the solution of the Quadratic Assignment Problem.

        Args:
            flow_matrix: Flow matrix between facilities.
            distance_matrix: Distance matrix between locations.
            assignment: Assignment of facilities to locations.
        """
        n_facilities = len(assignment)

        # Generate random coordinates for locations (for visualization purposes)
        np.random.seed(42)  # For reproducibility
        locations = np.random.rand(n_facilities, 2) * 10  # Scale coordinates for better visualization

        # Plot locations
        plt.figure(figsize=(8, 6))
        for loc_id, (x, y) in enumerate(locations):
            plt.scatter(x, y, color='blue', s=200, label='Locations' if loc_id == 0 else "", zorder=1)
            plt.text(x, y, f'L{loc_id + 1}', fontsize=12, ha='right', va='bottom', zorder=1)

        # Plot facilities and connections based on flow
        for facility_id, loc_id in enumerate(assignment):
            x, y = locations[loc_id]
            plt.scatter(x, y, color='red', s=100, marker='s', label='Facilities' if facility_id == 0 else "", zorder=2)
            plt.text(x, y, f'F{facility_id + 1}', fontsize=12, ha='left', va='top', zorder=2)

        # Draw lines between facilities based on flow
        for i in range(n_facilities):
            for j in range(i + 1, n_facilities):
                if flow_matrix[i, j] > 0:
                    loc_i = assignment[i]
                    loc_j = assignment[j]
                    plt.plot(
                        [locations[loc_i, 0], locations[loc_j, 0]],
                        [locations[loc_i, 1], locations[loc_j, 1]],
                        color='gray', linewidth=flow_matrix[i, j] / 10, alpha=0.5, zorder=0
                    )

        plt.title('QAP Solution: Facilities Assigned to Locations')
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')
        plt.legend()
        plt.grid(True)
        plt.show()

    def qap_evaluate(self, current_assignment: List[int], flow_matrix: np.ndarray, distance_matrix: np.ndarray, eva: Callable) -> List[int]:
        """
        Evaluate the next assignment for the Quadratic Assignment Problem using a constructive heuristic.

        Args:
            current_assignment: Current assignment of facilities to locations.
            flow_matrix: Flow matrix between facilities.
            distance_matrix: Distance matrix between locations.
            eva: The constructive heuristic function to select the next assignment.

        Returns:
            Updated assignment of facilities to locations.
        """
        # Use the heuristic to select the next assignment

        n_facilities = flow_matrix.shape[0]
        for _ in range(n_facilities):
            next_assignment = eva(current_assignment, flow_matrix, distance_matrix)

        return next_assignment

    def evaluate_qap(self, eva: Callable) -> float:
        """
        Evaluate the constructive heuristic for the Quadratic Assignment Problem.

        Args:
            instance_data: List of tuples containing the flow and distance matrices.
            n_ins: Number of instances to evaluate.
            eva: The constructive heuristic function to evaluate.

        Returns:
            The average total cost across all instances.
        """
        total_cost = 0

        for instance in self._datasets[:self.n_instance]:
            flow_matrix, distance_matrix = instance
            n_facilities = flow_matrix.shape[0]
            current_assignment = [-1] * n_facilities  # Initialize with no assignments
            current_assignment = self.qap_evaluate(current_assignment, flow_matrix, distance_matrix, eva)

            # Check if current_assignment is a feasible solution
            if -1 in current_assignment:
                raise ValueError("Feasibility check failed: Not all facilities are allocated.")
            if any(not (0 <= x < n_facilities) for x in current_assignment):
                raise ValueError("Feasibility check failed: Assignment values are out of range.")
            if len(set(current_assignment)) != n_facilities:
                raise ValueError("Feasibility check failed: Duplicate assignment values found.")

            # Calculate the total cost of the assignment
            cost = 0
            for i in range(n_facilities):
                for j in range(n_facilities):
                    cost += flow_matrix[i, j] * distance_matrix[current_assignment[i], current_assignment[j]]
            total_cost += cost

        average_cost = total_cost / self.n_instance
        return -average_cost  # We want to minimize the total cost


if __name__ == '__main__':

    def select_next_assignment(current_assignment: List[int], flow_matrix: np.ndarray, distance_matrix: np.ndarray) -> List[int]:
        """
        A greedy heuristic for the Quadratic Assignment Problem.

        Args:
            current_assignment: Current assignment of facilities to locations (-1 means unassigned).
            flow_matrix: Flow matrix between facilities.
            distance_matrix: Distance matrix between locations.

        Returns:
            Updated assignment of facilities to locations.
        """
        n_facilities = len(current_assignment)

        # Find the first unassigned facility and the first available location
        for facility in range(n_facilities):
            if current_assignment[facility] == -1:
                # Find the first available location
                for location in range(n_facilities):
                    if location not in current_assignment:
                        current_assignment[facility] = location
                        break
                break

        return current_assignment


    bp1d = QAPEvaluation()
    ave_bins = bp1d.evaluate_program('_', select_next_assignment)
    print(ave_bins)
