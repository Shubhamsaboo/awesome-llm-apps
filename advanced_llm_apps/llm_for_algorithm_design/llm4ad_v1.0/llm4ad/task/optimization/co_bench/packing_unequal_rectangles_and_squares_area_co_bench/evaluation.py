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
from llm4ad.task.optimization.co_bench.packing_unequal_rectangles_and_squares_area_co_bench.template import template_program, task_description

__all__ = ['PURSAEvaluationCB']


class PURSAEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Packing unequal rectangles and squares area")
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
        Evaluates a candidate solution for the "maximize total area" rectangle/square packing problem.
        The function expects:
          data: a dict with keys:
                - n        : int, number of items (rectangles or squares)
                - cx, cy   : floats, coordinates of the container center
                - R        : float, radius of the container
                - items    : list of tuples, each (L, W) giving dimensions of an item
                - shape    : string, either "rectangle" or "square"
                - rotation : bool, whether 90° rotation is allowed
          sol: a dict with key 'placements' containing a list of exactly n tuples.
               Each tuple is (x, y, theta) where:
                 - (x, y) is the center position for the item (if packed),
                 - theta is the rotation angle in degrees (counter-clockwise from the horizontal).
                 - For an unpacked item, x and y must be exactly -1 and theta is ignored (or should be 0).
        The evaluation process checks all feasibility constraints:
          1. The number of placements equals n.
          2. Each placement tuple must have three numerical values.
          3. For each item:
             - If it is "unpacked" (x == -1 and y == -1), it contributes no area.
             - If it is "packed" (x,y != -1), then:
                a. If rotation is not allowed, theta must be 0 (within a tiny tolerance).
                b. If rotation is allowed, theta must be either 0 or 90 (within tolerance).
                c. The entire item (with given dimensions and rotation) must lie completely inside
                   the circular container (centered at (cx, cy) with radius R).
          4. No two packed items may overlap (their interiors should be disjoint).
        If any constraint is violated, the function raises a ValueError with an appropriate message.
        If all constraints are met, the function returns the total area of the packed items.
        (This is the score that we wish to maximize.)
        Note: The evaluation is designed to be robust against malicious modifications
              by the solve function. Only valid solutions (with zero penalties) receive a score.
        """

        # Tolerances for numerical comparisons
        tol = 1e-5
        angle_tol = 1e-3  # tolerance for angle comparisons in degrees

        # Unpack input data
        try:
            n = kwargs['n']
            cx, cy = float(kwargs['cx']), float(kwargs['cy'])
            R = float(kwargs['R'])
            items = kwargs['items']
            shape = kwargs['shape'].lower()
            rotation_allowed = bool(kwargs['rotation'])
        except KeyError as e:
            raise ValueError(f"Missing input data key: {e}")

        if len(items) != n:
            raise ValueError("Length of items list must equal n.")

        # Unpack solution
        placements = kwargs.get('placements', None)
        if placements is None:
            raise ValueError("Solution does not contain key 'placements'.")
        if not isinstance(placements, list) or len(placements) != n:
            raise ValueError("The 'placements' list must contain exactly n tuples.")

        # Helper: Given a placement (x, y, theta in degrees) and item dimensions (L, W),
        # compute the four vertices of the rectangle after rotation.
        def compute_vertices(x, y, L, W, theta_deg):
            theta = math.radians(theta_deg)
            # Local coordinates of corners before rotation:
            local_corners = [(L / 2, W / 2),
                             (L / 2, -W / 2),
                             (-L / 2, W / 2),
                             (-L / 2, -W / 2)]
            vertices = []
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)
            for dx, dy in local_corners:
                # Apply rotation:
                dx_r = dx * cos_t - dy * sin_t
                dy_r = dx * sin_t + dy * cos_t
                vertices.append((x + dx_r, y + dy_r))
            return vertices

        # Helper: For an item with placement (x,y,theta) and dimensions (L,W),
        # compute its axis-aligned bounding box.
        # Since allowed rotations are only 0 or 90 degrees (if rotation is allowed),
        # the rectangle remains axis-aligned.
        def compute_aabb(x, y, L, W, theta_deg):
            # Enforce only 0 or 90: if theta is nearly 90, swap dimensions.
            if abs(theta_deg) < angle_tol:
                half_L, half_W = L / 2, W / 2
            elif abs(theta_deg - 90) < angle_tol:
                half_L, half_W = W / 2, L / 2
            else:
                # Should not happen; safeguard.
                raise ValueError("Invalid rotation angle. Allowed angles are 0 or 90 degrees.")
            return (x - half_L, x + half_L, y - half_W, y + half_W)

        total_area = 0.0
        placed_items = []  # List of dicts: { 'aabb': (xmin,xmax,ymin,ymax), 'vertices': [...] }

        # Process each item
        for i in range(n):
            # Check placement tuple structure
            try:
                placement = placements[i]
                if not (isinstance(placement, (list, tuple)) and len(placement) == 3):
                    raise ValueError(f"Placement for item {i} must be a tuple/list of three numbers.")
                x, y, theta = float(placement[0]), float(placement[1]), float(placement[2])
            except Exception as e:
                raise ValueError(f"Invalid placement for item {i}: {e}")

            L, W = items[i]
            # For squares, check that L == W (within tolerance)
            if shape == "square" and abs(L - W) > tol:
                raise ValueError(f"Item {i} is marked as square but dimensions differ: L={L}, W={W}")

            # Determine if the item is packed.
            # Convention: If x == -1 and y == -1, item is not placed.
            if abs(x + 1) < tol and abs(y + 1) < tol:
                # Unpacked item: skip (area = 0). Optionally, enforce theta = 0.
                if abs(theta) > angle_tol:
                    raise ValueError(f"Unpacked item {i} must have theta equal to 0.")
                continue

            # Packed item: check rotation feasibility.
            if not rotation_allowed:
                if abs(theta) > angle_tol:
                    raise ValueError(f"Rotation is not allowed, but item {i} has theta = {theta}.")
            else:
                # If rotation is allowed, then theta must be 0 or 90.
                if not (abs(theta) < angle_tol or abs(theta - 90) < angle_tol):
                    raise ValueError(
                        f"Item {i} has invalid rotation angle {theta}. Allowed values are 0 or 90 degrees.")

            # Compute the vertices for the placed rectangle.
            vertices = compute_vertices(x, y, L, W, theta)
            # Check each vertex lies inside the container circle.
            for vx, vy in vertices:
                # Euclidean distance from container center (cx, cy)
                if (vx - cx) ** 2 + (vy - cy) ** 2 > R ** 2 + tol:
                    raise ValueError(f"Item {i} has a vertex at ({vx:.4f},{vy:.4f}) outside the container.")

            # Compute axis-aligned bounding box (since rectangle is axis-aligned if theta in {0,90})
            xmin, xmax, ymin, ymax = compute_aabb(x, y, L, W, theta)

            # Save the item details for later overlap checking.
            placed_items.append({
                'index': i,
                'aabb': (xmin, xmax, ymin, ymax),
                'vertices': vertices,
                'area': L * W
            })
            total_area += L * W

        # Check for pairwise overlap among all placed items.
        num_placed = len(placed_items)
        for i in range(num_placed):
            aabb_i = placed_items[i]['aabb']
            xmin_i, xmax_i, ymin_i, ymax_i = aabb_i
            for j in range(i + 1, num_placed):
                aabb_j = placed_items[j]['aabb']
                xmin_j, xmax_j, ymin_j, ymax_j = aabb_j
                # Compute overlap in x and y
                overlap_x = max(0.0, min(xmax_i, xmax_j) - max(xmin_i, xmin_j))
                overlap_y = max(0.0, min(ymax_i, ymax_j) - max(ymin_i, ymin_j))
                if overlap_x * overlap_y > tol:
                    raise ValueError(f"Items {placed_items[i]['index']} and {placed_items[j]['index']} overlap.")

        return total_area

    def norm_score(self, results):
        optimal_scores = {
            "rect1.txt": [37.6878, 37.9687],
            "rect2.txt": [84.4446, 84.7008],
            "rect3.txt": [103.4802, 110.3253],
            "square1.txt": [51.7583],
            "square2.txt": [109.8363],
            "square3.txt": [103.0963],
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






