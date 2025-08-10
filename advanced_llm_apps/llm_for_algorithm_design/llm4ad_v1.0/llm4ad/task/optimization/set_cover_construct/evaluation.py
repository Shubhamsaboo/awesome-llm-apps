# Module Name: SCPEvaluation
# Last Revision: 2025/2/16
# Description: Evaluates the Set Covering Problem (SCP).
#       The SCP involves selecting a minimum number of subsets from a collection that covers all elements in a universal set.
#       This module is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Parameters:
#   - timeout_seconds: Maximum allowed time (in seconds) for the evaluation process: int (default: 30).
#   - n_instance: Number of problem instances to generate: int (default: 5).
#   - n_elements: Number of elements in the universal set: int (default: 10).
#   - n_subsets: Number of subsets in the collection: int (default: 15).
#   - max_subset_size: Maximum size of each subset: int (default: 5).
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
from typing import Any, List, Tuple, Callable
import numpy as np
import matplotlib.pyplot as plt

from llm4ad.base import Evaluation
from llm4ad.task.optimization.set_cover_construct.get_instance import GetData
from llm4ad.task.optimization.set_cover_construct.template import template_program, task_description

__all__ = ['SCPEvaluation']

import matplotlib.pyplot as plt


class SCPEvaluation(Evaluation):
    """Evaluator for the Set Covering Problem."""

    def __init__(self,
                 timeout_seconds=30,
                 n_instance: int = 16,
                 n_elements: int = 50,
                 n_subsets: int = 50,
                 max_subset_size: int = 8,
                 **kwargs):
        """
        Args:
            n_instance: Number of instances to generate.
            n_elements: Number of elements in the universal set.
            n_subsets: Number of subsets in the collection.
            max_subset_size: Maximum size of each subset.
        """
        super().__init__(
            template_program=template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds
        )

        self.n_instance = n_instance
        self.n_elements = n_elements
        self.n_subsets = n_subsets
        self.max_subset_size = max_subset_size

        getData = GetData(self.n_instance, self.n_elements, self.n_subsets, self.max_subset_size)
        self._datasets = getData.generate_instances()

    def evaluate_program(self, program_str: str, callable_func: Callable) -> Any | None:
        """
        Evaluate a constructive heuristic for the Set Covering Problem.

        Args:
            program_str: A string representation of the heuristic (unused here).
            callable_func: The constructive heuristic function to evaluate.

        Returns:
            The average number of subsets used.
        """
        return self.evaluate(callable_func)

    def plot_solution(self, universal_set: List[int], selected_subsets: List[List[int]], all_subsets: List[List[int]]):
        """
        Plot the final solution of the Set Covering Problem, including selected and unselected subsets.

        Args:
            universal_set: The universal set of elements.
            selected_subsets: The list of selected subsets that cover the universal set.
            all_subsets: The list of all subsets (including unselected ones).
        """
        # Create a mapping of elements to their positions for plotting
        element_positions = {element: idx for idx, element in enumerate(universal_set)}

        # Plot the universal set
        plt.figure(figsize=(10, 6))
        plt.scatter([element_positions[element] for element in universal_set], [0] * len(universal_set),
                    color='blue', label='Universal Set', s=100)

        # Plot the selected subsets
        for subset_idx, subset in enumerate(selected_subsets):
            plt.scatter([element_positions[element] for element in subset], [subset_idx + 1] * len(subset),
                        label=f'Selected Subset {subset_idx + 1}', s=100, marker='o', edgecolor='black')

        # Plot the unselected subsets
        unselected_subsets = [subset for subset in all_subsets if subset not in selected_subsets]
        for subset_idx, subset in enumerate(unselected_subsets):
            plt.scatter([element_positions[element] for element in subset], [subset_idx + len(selected_subsets) + 1] * len(subset),
                        label=f'Unselected Subset {subset_idx + 1}', s=100, marker='o', edgecolor='black', facecolor='none')

        # Add annotations and labels
        y_labels = ['Universal Set'] + [f'Selected Subset {i + 1}' for i in range(len(selected_subsets))] + \
                   [f'Unselected Subset {i + 1}' for i in range(len(unselected_subsets))]
        plt.yticks(range(len(y_labels)), y_labels)
        plt.xlabel('Elements')
        plt.title('Set Covering Problem Solution')
        plt.legend(loc='upper right')
        plt.grid(True, axis='x')
        plt.tight_layout()
        plt.show()

    def cover_subsets(self, universal_set: List[int], subsets: List[List[int]], eva: Callable) -> Tuple[int, List[List[int]]]:
        """
        Select subsets to cover the universal set using a constructive heuristic.

        Args:
            universal_set: The universal set of elements to cover.
            subsets: A list of subsets, where each subset is a list of elements.
            eva: The constructive heuristic function to select the next subset.

        Returns:
            A tuple containing:
            - The total number of subsets used.
            - A list of selected subsets.
        """
        selected_subsets = []  # List to store the selected subsets
        remaining_elements = set(universal_set)  # Set to track uncovered elements
        remaining_subsets = subsets.copy()  # Copy of subsets to track remaining subsets

        while remaining_elements:
            # Use the heuristic to select the next subset
            selected_subset = eva(selected_subsets, remaining_subsets, list(remaining_elements))

            if selected_subset is None:
                break  # No more subsets to select

            # Add the selected subset to the list of selected subsets
            selected_subsets.append(selected_subset)
            # Remove the covered elements from the remaining elements
            remaining_elements -= set(selected_subset)
            # Remove the selected subset from the remaining subsets
            remaining_subsets.remove(selected_subset)

        # Calculate the number of subsets used
        used_subsets = len(selected_subsets)
        return used_subsets, selected_subsets

    def evaluate(self, eva: Callable) -> float:
        """
        Evaluate the constructive heuristic for the Set Covering Problem.

        Args:
            instance_data: List of tuples containing the universal set and subsets.
            n_ins: Number of instances to evaluate.
            eva: The constructive heuristic function to evaluate.

        Returns:
            The average number of subsets used across all instances.
        """
        total_subsets = 0

        for instance in self._datasets[:self.n_instance]:
            universal_set, subsets = instance
            num_subsets, _ = self.cover_subsets(universal_set, subsets, eva)
            total_subsets += num_subsets

        average_subsets = total_subsets / self.n_instance
        return -average_subsets  # Negative because we want to minimize the number of subsets


if __name__ == '__main__':

    def select_next_subset(selected_subsets: List[List[int]], remaining_subsets: List[List[int]], remaining_elements: List[int]) -> List[int] | None:
        """
        A heuristic for the Set Covering Problem.

        Args:
            selected_subsets: List of already selected subsets.
            remaining_subsets: List of remaining subsets to choose from.
            remaining_elements: List of elements still to be covered.

        Returns:
            The next subset to select, or None if no subset can cover any remaining elements.
        """
        max_covered = 0
        best_subset = None

        for subset in remaining_subsets:
            # Calculate the number of uncovered elements this subset covers
            covered = len(set(subset).intersection(remaining_elements))
            if covered > max_covered:
                max_covered = covered
                best_subset = subset

        return best_subset


    bp1d = SCPEvaluation()
    ave_bins = bp1d.evaluate_program('_', select_next_subset)
    print(ave_bins)
