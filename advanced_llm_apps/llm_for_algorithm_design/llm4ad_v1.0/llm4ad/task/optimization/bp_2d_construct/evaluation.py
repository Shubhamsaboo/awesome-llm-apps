# Module Name: BP2DEvaluation
# Last Revision: 2025/2/16
# Description: Evaluates constructive heuristic for 2-dimensional bin packing problem.
#               Given a set of bins and items, iteratively assign one item to feasible bins.
#               Design the optimal heuristic in each iteration to minimize the used bins.
#              This module is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
# 
# Parameters:
#    -   n_bins: number of bins: int (default: 10).
#    -   n_instance: number of instances: int (default: 16).
#    -   n_items: number of items: int (default: 10).
#    -   bin_width: width of bins: int (default: 100).
#    -   bin_height: height of bins: int (default: 100).
#    -   timeout_seconds: int - Maximum allowed time (in seconds) for the evaluation process (default: 60).
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
from typing import List, Tuple, Callable, Any
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from llm4ad.base import Evaluation
from llm4ad.task.optimization.bp_2d_construct.get_instance import GetData
from llm4ad.task.optimization.bp_2d_construct.template import template_program, task_description

__all__ = ['BP2DEvaluation']


class BP2DEvaluation(Evaluation):
    """Evaluator for the 2D Bin Packing Problem."""

    def __init__(self,
                 timeout_seconds: int = 120,
                 n_bins: int = 100,
                 n_instance: int = 8,
                 n_items: int = 100,
                 bin_width: int = 100,
                 bin_height: int = 100,
                 **kwargs):
        """
        Args:
            n_bins: The number of available bins at the beginning.
        """
        super().__init__(
            template_program=template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds
        )

        self.n_instance = n_instance
        self.n_items = n_items
        self.n_bins = n_bins
        self.bin_width = bin_width
        self.bin_height = bin_height
        getData = GetData(self.n_instance, self.n_items, self.bin_width, self.bin_height)
        self._datasets = getData.generate_instances()

    def plot_solution(self, bins: List[List[Tuple[Tuple[int, int], Tuple[int, int]]]], bin_dimensions: Tuple[int, int]):
        """
        Plot the final packing solution for 2D bin packing.

        Args:
            bins: A list of bins, where each bin is a list of tuples containing the corner and dimensions of packed items.
            bin_dimensions: A tuple representing the (width, height) of the bin.
        """
        # Only plot the used bins
        num_bins = sum(1 for bin_content in bins if bin_content) + 5
        bins = bins[:num_bins]
        max_bins_per_row = 5
        num_rows = (num_bins + max_bins_per_row - 1) // max_bins_per_row  # Calculate the number of rows needed

        fig, axes = plt.subplots(num_rows, max_bins_per_row, figsize=(5 * max_bins_per_row, 5 * num_rows))

        # Flatten the axes array if there are multiple rows
        if num_rows > 1:
            axes = axes.flatten()
        else:
            axes = [axes]  # Ensure axes is a list for consistency

        for i, bin_content in enumerate(bins):
            ax = axes[i]
            ax.set_xlim(0, bin_dimensions[0])
            ax.set_ylim(0, bin_dimensions[1])
            ax.set_title(f"Bin {i + 1}")
            ax.set_aspect('equal')

            # Draw the bin boundary
            bin_rect = patches.Rectangle((0, 0), bin_dimensions[0], bin_dimensions[1], linewidth=2, edgecolor='black', facecolor='none')
            ax.add_patch(bin_rect)

            # Draw each item in the bin
            for corner, (width, height) in bin_content:
                item_rect = patches.Rectangle(corner, width, height, linewidth=1, edgecolor='blue', facecolor='lightblue', alpha=0.6)
                ax.add_patch(item_rect)
                # Add text to label the item
                ax.text(corner[0] + width / 2, corner[1] + height / 2, f"{width}x{height}", ha='center', va='center', fontsize=8)

        # Hide unused axes if the number of bins is not a multiple of max_bins_per_row
        for j in range(num_bins, num_rows * max_bins_per_row):
            axes[j].axis('off')

        plt.tight_layout()
        plt.show()

    def pack_items_2d(self, item_dimensions: List[Tuple[int, int]], bin_dimensions: Tuple[int, int], eva: Callable, n_bins: int) -> Tuple[int, List[List[Tuple[int, int]]]]:
        """
        Pack items into bins using a constructive heuristic for the 2D Bin Packing Problem.
        The bins are represented as a discrete point matrix to track feasible areas.

        Args:
            item_dimensions: A list of tuples, where each tuple represents the (width, height) of an item.
            bin_dimensions: A tuple representing the (width, height) of the bin.
            eva: The constructive heuristic function to select the next item and bin.
            n_bins: The number of available bins at the beginning.

        Returns:
            A tuple containing:
            - The total number of bins used.
            - A list of bins, where each bin is a list of item dimensions.
        """
        bins = [[] for _ in range(n_bins)]  # Initialize n_bins empty bins
        remaining_items = item_dimensions.copy()  # Copy of item dimensions to track remaining items
        # Initialize the point matrix for each bin (0: unoccupied, 1: occupied)
        point_matrices = [[[0 for _ in range(bin_dimensions[1])] for _ in range(bin_dimensions[0])] for _ in range(n_bins)]

        while remaining_items:
            # Use the heuristic to select the next item and bin
            selected_item, selected_bin = eva(remaining_items, point_matrices)

            if selected_bin is not None:
                # Find a feasible position for the selected item in the selected bin
                placed = False
                for x in range(bin_dimensions[0] - selected_item[0] + 1):
                    for y in range(bin_dimensions[1] - selected_item[1] + 1):
                        # Check the four edges of the item
                        top_edge = all(point_matrices[selected_bin][x + dx][y] == 0 for dx in range(selected_item[0]))
                        bottom_edge = all(point_matrices[selected_bin][x + dx][y + selected_item[1] - 1] == 0 for dx in range(selected_item[0]))
                        left_edge = all(point_matrices[selected_bin][x][y + dy] == 0 for dy in range(selected_item[1]))
                        right_edge = all(point_matrices[selected_bin][x + selected_item[0] - 1][y + dy] == 0 for dy in range(selected_item[1]))

                        if top_edge and bottom_edge and left_edge and right_edge:
                            # Place the item at this position
                            for dx in range(selected_item[0]):
                                for dy in range(selected_item[1]):
                                    point_matrices[selected_bin][x + dx][y + dy] = 1
                            bins[selected_bin].append(((x, y), selected_item))
                            placed = True
                            break
                    if placed:
                        break
                if not placed:
                    # If the item cannot be placed in the selected bin, try other bins
                    for i in range(len(bins)):
                        if placed:
                            break
                        selected_bin = i
                        for x in range(bin_dimensions[0] - selected_item[0] + 1):
                            for y in range(bin_dimensions[1] - selected_item[1] + 1):
                                # Check only the four corners of the item
                                corners = [
                                    (x, y),
                                    (x + selected_item[0] - 1, y),
                                    (x, y + selected_item[1] - 1),
                                    (x + selected_item[0] - 1, y + selected_item[1] - 1)
                                ]
                                if all(point_matrices[selected_bin][cx][cy] == 0 for cx, cy in corners):
                                    # Place the item at this position
                                    for dx in range(selected_item[0]):
                                        for dy in range(selected_item[1]):
                                            point_matrices[selected_bin][x + dx][y + dy] = 1
                                    bins[selected_bin].append(((x, y), selected_item))
                                    placed = True
                                    break
                            if placed:
                                break
            else:
                # If no feasible bin is found, stop packing (no more bins available)
                break

            # Remove the selected item from the remaining items
            remaining_items.remove(selected_item)

        # Calculate the number of bins used (bins that contain at least one item)
        used_bins = sum(1 for bin_content in bins if bin_content)
        return used_bins, bins

    def evaluate_2d(self, eva: Callable) -> float:
        """
        Evaluate the constructive heuristic for the 2D Bin Packing Problem.

        Args:
            eva: callable function of constructive heuristic.

        Returns:
            The average number of bins used across all instances.
        """
        total_bins = 0

        for instance in self._datasets[:self.n_instance]:
            item_dimensions, bin_dimensions = instance
            num_bins, _ = self.pack_items_2d(item_dimensions, bin_dimensions, eva, self.n_bins)
            total_bins += num_bins

        average_bins = total_bins / self.n_instance
        return -average_bins  # Negative because we want to minimize the number of bins

    def evaluate_program(self, program_str: str, callable_func: Callable) -> Any | None:
        return self.evaluate_2d(callable_func)


if __name__ == '__main__':

    def determine_next_assignment(remaining_items: List[Tuple[int, int]], feasible_corners: List[List[Tuple[int, int]]]) -> Tuple[Tuple[int, int], int]:
        """
        A simple heuristic function to select the next item and bin for 2D bin packing.

        Args:
            remaining_items: A list of tuples representing the (width, height) of remaining items.
            feasible_corners: A list of lists, where each inner list contains the feasible corners for a bin.

        Returns:
            A tuple containing:
            - The selected item (width, height).
            - The index of the selected bin (or None if no bin is feasible).
        """
        # Step 1: Select the largest item by area
        selected_item = max(remaining_items, key=lambda x: x[0] * x[1])

        # Step 2: Select the bin with the most feasible corners
        max_corners = -1
        selected_bin = None
        for i, corners in enumerate(feasible_corners):
            if len(corners) > max_corners:
                max_corners = len(corners)
                selected_bin = i

        # If no bin has feasible corners, return None for the bin
        if max_corners == 0:
            selected_bin = None

        return selected_item, selected_bin


    bp2d = BP2DEvaluation()
    ave_bins = bp2d.evaluate_program('_', determine_next_assignment)
    print(ave_bins)
