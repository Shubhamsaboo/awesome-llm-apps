# References:
#   - Sun, W., Feng, S., Li, S., & Yang, Y. Co-bench: Benchmarking language
#       model agents in algorithm search for combinatorial optimization.
#       arXiv preprint arXiv:2504.04310 (2025).
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

import math
from typing import Any
import numpy as np
from llm4ad.base import Evaluation
from llm4ad.task.optimization.co_bench.utils import load_subdir_as_text
from llm4ad.task.optimization.co_bench.packing_unequal_rectangles_and_squares_co_bench.template import template_program, task_description

__all__ = ['PURSEvaluationCB']


class PURSEvaluationCB(Evaluation):

    def __init__(self,
                 timeout_seconds=50,
                 **kwargs):

        """
            Args:
                None
            Raises:
                AttributeError: If the data key does not exist.
                FileNotFoundError: If the specified data file is not found.
        """

        super().__init__(
            template_program=template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds
        )

        # Load datasets from Hugging Face
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Packing unequal rectangles and squares")
        self._datasets = {}
        for filename in dataset:
            # Join all text rows into a single string
            text_content = '\n'.join([row['text'] for row in dataset[filename]])
            self._datasets[filename] = text_content

    def evaluate_program(self, program_str: str, callable_func: callable, **kwargs) -> Any | None:
        return self.evaluate(callable_func)

    def evaluate(self, eva: callable) -> float | None:
        ins_cases = []
        for case_id, ins in enumerate(self._datasets.values()):
            ins_cases.append(self.load_data(ins))

        fitness_list = []
        try:
            for i in ins_cases:
                for j in i:
                    result = eva(j['n'], j['cx'], j['cy'], j['R'], j['items'], j['shape'], j['rotation'])
                    fitness = self.eval_func(n=j['n'], cx=j['cx'], cy=j['cy'], R=j['R'], items=j['items'], shape=j['shape'], rotation=j['rotation'], placements=result['placements'])
                    fitness_list.append(fitness)

            return np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Reads input string content that may contain multiple cases for the packing problem.
        Each case is formatted as follows:
          - A header line with four values: n, cx, cy, R
              n   : number of items (rectangles or squares)
              cx, cy : container center coordinates
              R   : container radius
          - Next n non-empty lines: each line represents an item:
              * For a square: one number (side length) — interpreted as (side, side)
              * For a rectangle: two numbers (length and width)
        Returns:
          A list of cases. Each case is a dictionary with the following keys:
             - 'n'    : int, number of items
             - 'cx'   : float, x-coordinate of container center
             - 'cy'   : float, y-coordinate of container center
             - 'R'    : float, container radius
             - 'items': list of tuples, where each tuple is (L, W) for the respective item.
        """
        cases = []
        lines = [line.strip() for line in input_string.split('\n') if line.strip() != '']

        i = 0
        while i < len(lines):
            # Parse header line for one case
            header_tokens = lines[i].split()
            if len(header_tokens) < 4:
                raise ValueError("Header line must contain at least 4 values: n, cx, cy, R.")
            n = int(header_tokens[0])
            cx = float(header_tokens[1])
            cy = float(header_tokens[2])
            R = float(header_tokens[3])
            i += 1

            # Ensure there are enough lines for all items
            if i + n > len(lines):
                raise ValueError("Insufficient item lines for a case.")

            items = []
            shape = None
            for j in range(n):
                tokens = lines[i].split()
                if len(tokens) == 1:
                    side = float(tokens[0])
                    items.append((side, side))
                    shape = 'square'
                elif len(tokens) >= 2:
                    length = float(tokens[0])
                    width = float(tokens[1])
                    items.append((length, width))
                    shape = 'rectangle'
                else:
                    raise ValueError(f"Item data format error at line {i + 1}.")
                i += 1

            # Append the parsed case as a dictionary
            if shape == 'rectangle':
                cases.append({
                    'n': n,
                    'cx': cx,
                    'cy': cy,
                    'R': R,
                    'items': items,
                    'shape': shape,
                    'rotation': False
                })
                cases.append({
                    'n': n,
                    'cx': cx,
                    'cy': cy,
                    'R': R,
                    'items': items,
                    'shape': shape,
                    'rotation': True
                })
            else:
                cases.append({
                    'n': n,
                    'cx': cx,
                    'cy': cy,
                    'R': R,
                    'items': items,
                    'shape': shape,
                    'rotation': False

                })

        return cases

    def eval_func(self, **kwargs):
        """
        Evaluates a solution for the "maximise number of items packed" rectangle (or square)
        packing problem in a circular container.
        Parameters:
          input_data: dict with keys:
             - n         : int, total number of available items.
             - cx, cy    : floats, coordinates of the container center.
             - R         : float, container radius.
             - items     : list of tuples, where each tuple (L, W) gives the dimensions of an item.
                           (For squares, L == W.)
             - shape     : str, either "rectangle" or "square".
             - rotation  : bool, whether 90° rotation is allowed.
          solution_output: dict with key 'placements' containing a list of exactly n tuples.
             Each tuple is (x, y, theta), where:
               - (x, y) are the center coordinates.
               - theta is the rotation angle in degrees (counter-clockwise from horizontal).
               - For any item that is not packed, x and y should be set to -1 (theta can be 0).
        Returns:
          score: int, the number of valid (packed) items.
        Raises:
          ValueError: if any constraint is violated.
        """
        # Unpack input parameters.
        tol = 1e-5
        n = kwargs.get("n")
        cx = kwargs.get("cx")
        cy = kwargs.get("cy")
        R = kwargs.get("R")
        items = kwargs.get("items")  # list of (L, W)
        shape = kwargs.get("shape").lower()  # "rectangle" or "square"
        rotation_allowed = kwargs.get("rotation")

        placements = kwargs.get("placements")

        # Check that exactly n placements are provided.
        if not isinstance(placements, list) or len(placements) != n:
            raise ValueError("The output must contain exactly n placements.")

        # List to hold the geometry of each packed item for later overlap checking.
        # For each packed item, we will store a tuple: (xmin, xmax, ymin, ymax)
        packed_rectangles = []

        score = 0  # Count of packed items.

        for idx, placement in enumerate(placements):
            if (not isinstance(placement, (list, tuple))) or len(placement) != 3:
                raise ValueError(f"Placement {idx} must be a tuple of (x, y, theta).")
            x, y, theta = placement

            # Check unpacked indicator: if x == -1 and y == -1 then item is not packed.
            if x == -1 and y == -1:
                # Unpacked item; theta is ignored. Continue.
                continue

            # Otherwise, the item is packed.
            score += 1

            # --- Check rotation value.
            # If rotation is not allowed then theta must be 0.
            # If rotation is allowed, we require theta to be either 0 or 90 (within a small tolerance).
            if rotation_allowed:
                if not (math.isclose(theta, 0, abs_tol=1e-3) or math.isclose(theta, 90, abs_tol=1e-3)):
                    raise ValueError(f"Item {idx}: rotation angle must be 0 or 90 degrees when rotation is allowed.")
            else:
                if not math.isclose(theta, 0, abs_tol=1e-3):
                    raise ValueError(f"Item {idx}: rotation angle must be 0 when rotation is not allowed.")

            # --- Determine the effective dimensions of the item.
            L, W = items[idx]
            # For squares, ensure consistency.
            if shape == "square" and not math.isclose(L, W, abs_tol=1e-3):
                raise ValueError(f"Item {idx}: For square packing, dimensions must be equal.")

            # If rotated by 90, swap dimensions.
            if rotation_allowed and math.isclose(theta, 90, abs_tol=1e-3):
                eff_L, eff_W = W, L
            else:
                eff_L, eff_W = L, W

            half_L = eff_L / 2.0
            half_W = eff_W / 2.0

            # --- Compute the coordinates of the four corners.
            # Since theta is either 0 or 90, the rectangle remains axis aligned.
            # For theta==0: corners are (x ± half_L, y ± half_W).
            # For theta==90: same structure because dimensions have been swapped.
            corners = [
                (x - half_L, y - half_W),
                (x - half_L, y + half_W),
                (x + half_L, y - half_W),
                (x + half_L, y + half_W)
            ]

            # --- Check that every corner is inside the container.
            for corner in corners:
                cx_corner, cy_corner = corner
                # Distance from the container center (cx, cy)
                dist = math.hypot(cx_corner - cx, cy_corner - cy)
                if dist > R + tol:  # use a small tolerance
                    raise ValueError(f"Item {idx}: Corner {corner} lies outside the container.")

            # --- Store the axis-aligned bounding box for overlap checking.
            # (Since the rectangles are axis aligned, the bounding box is the rectangle itself.)
            xmin = x - half_L
            xmax = x + half_L
            ymin = y - half_W
            ymax = y + half_W
            current_rect = (xmin, xmax, ymin, ymax)

            # --- Check for overlap with previously packed items.
            for jdx, other_rect in enumerate(packed_rectangles):
                oxmin, oxmax, oymin, oymax = other_rect
                # Two axis-aligned rectangles do not overlap if one is to the left
                # or one is above the other.
                if not (xmax <= oxmin + tol or xmin >= oxmax - tol or
                        ymax <= oymin + tol or ymin >= oymax - tol):
                    raise ValueError(f"Item {idx} overlaps with an already packed item (index {jdx}).")

            # Save the current rectangle for future overlap checking.
            packed_rectangles.append(current_rect)

        return score

    def norm_score(self, results):
        optimal_scores = {
            "rect1.txt": [7, 7],
            "rect2.txt": [11, 12],
            "rect3.txt": [19, 20],
            "square1.txt": [6],
            "square2.txt": [14],
            "square3.txt": [23],
        }

        normed = {}
        for case, (scores, error_message) in results.items():
            if case not in optimal_scores:
                continue  # Skip if there's no optimal score defined.
            optimal_list = optimal_scores[case]
            normed_scores = []
            # Compute normalized score for each index.
            for idx, score in enumerate(scores):
                if isinstance(score, (int, float)):
                    normed_scores.append(score / optimal_list[idx])
                else:
                    normed_scores.append(score)
            normed[case] = (normed_scores, error_message)
        return normed






