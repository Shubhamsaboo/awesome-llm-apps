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

from typing import Any
import numpy as np
from llm4ad.base import Evaluation
from llm4ad.task.optimization.co_bench.utils import load_subdir_as_text
from llm4ad.task.optimization.co_bench.constrained_guillotine_cutting_co_bench.template import template_program, task_description

__all__ = ['CGCEvaluationCB']


class CGCEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Constrained guillotine cutting")
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
                    result = eva(j['m'], j['stock_length'], j['stock_width'], j['piece_types'])
                    fitness = self.eval_func(j['m'], j['stock_length'], j['stock_width'], j['piece_types'], result['total_value'], result['placements'])
                    fitness_list.append(fitness)

            return np.mean(fitness_list)  # itself is a maximize problem

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Loads one or more cases from an input file for the Constrained Guillotine Cutting problem.
        The input file contains one or more cases concatenated together. Each case is structured as follows:
          - The first token: an integer m (the number of piece types).
          - The next two tokens: stock_length and stock_width.
          - Then 4*m tokens follow, where each group of 4 tokens represents a piece type:
                piece_length, piece_width, maximum permitted count, piece_value.
        Parameters:
          input_path (str): Path to the input TXT file.
        Returns:
          List[dict]: A list where each element is a dictionary with the following keys:
              - m: int, number of piece types.
              - stock_length: int, length of the stock sheet.
              - stock_width: int, width of the stock sheet.
              - piece_types: list of dicts, each with keys 'length', 'width', 'max', 'value'.
        """
        cases = []
        content = input_string
        tokens = content.split()
        pos = 0
        total_tokens = len(tokens)

        while pos < total_tokens:
            # Ensure there are at least 3 tokens to read m, stock_length, stock_width
            if pos + 3 > total_tokens:
                raise ValueError("Insufficient data for a new case.")
            try:
                m = int(tokens[pos])
                stock_length = int(tokens[pos + 1])
                stock_width = int(tokens[pos + 2])
            except:
                raise ValueError("Error parsing m, stock_length, or stock_width.")
            pos += 3

            # There must be 4*m tokens for the piece types.
            if pos + 4 * m > total_tokens:
                raise ValueError("Not enough tokens for piece types in one case.")

            piece_types = []
            for i in range(m):
                try:
                    p_length = int(tokens[pos])
                    p_width = int(tokens[pos + 1])
                    max_count = int(tokens[pos + 2])
                    p_value = int(tokens[pos + 3])
                except:
                    raise ValueError("Error parsing piece type data.")
                piece_types.append({
                    'length': p_length,
                    'width': p_width,
                    'max': max_count,
                    'value': p_value
                })
                pos += 4

            case_data = {
                "m": m,
                "stock_length": stock_length,
                "stock_width": stock_width,
                "piece_types": piece_types
            }
            cases.append(case_data)

        return cases

    def eval_func(self, m, stock_length, stock_width, piece_types, total_value, placements):
        """
        Evaluates a solution for the Fixed Orientation Guillotine Cutting problem by verifying all constraints.
        Raises an error immediately upon any constraint violation.
        Parameters:
          m (int): Number of piece types.
          stock_length (int): Length of the stock rectangle.
          stock_width (int): Width of the stock rectangle.
          piece_types (list of dict): Each dict has keys:
              'length': int, piece length.
              'width' : int, piece width.
              'max'   : int, maximum permitted count for the piece type.
              'value' : int, value of the piece.
          total_value (int): The reported total value from the solution.
          placements (list): List of placements. Each placement is a tuple or list of 6 integers:
                (piece_type_index, x, y, placed_length, placed_width, orientation_flag)
                where orientation_flag must be 0 (rotation not allowed).
        Returns:
          int: The computed total value if the solution is valid.
        Constraints verified:
          - Each placement is a well-formed 6-tuple of integers.
          - The piece type index is within the valid range.
          - The orientation flag is 0 (rotation is not allowed).
          - The placed dimensions match the expected dimensions.
          - Each piece is completely within the stock boundaries.
          - No two pieces overlap.
          - The count of pieces of each type does not exceed its allowed maximum.
          - The reported total_value exactly equals the computed sum of placed piece values.
          - The set of placements satisfies the guillotine cutting condition.
        """

        # Helper function: Check guillotine feasibility recursively.
        def is_guillotine(rects, bx, by, ex, ey):
            """
            Recursively checks if the collection of placed rectangles (rects) in the box
            defined by (bx, by) - (ex, ey) is guillotine separable.
            A set of placements is considered guillotine feasible if there exists at least one straight cut
            (vertical or horizontal) that does not slice through any rectangle, and the property holds recursively
            on the resulting subregions. Empty regions or regions exactly matching a placed piece are considered valid.
            """
            # If there are no pieces, the region is trivially guillotine separable.
            if not rects:
                return True
            # If a single rectangle exactly covers the region, it is guillotine separable.
            if len(rects) == 1:
                r = rects[0]
                if r[0] == bx and r[1] == by and r[2] == ex and r[3] == ey:
                    return True

            # Try vertical cuts.
            for x in range(bx + 1, ex):
                # A vertical cut at x is valid if no rectangle is cut by the line.
                if all((r[2] <= x or r[0] >= x) for r in rects):
                    left_rects = [r for r in rects if r[2] <= x]
                    right_rects = [r for r in rects if r[0] >= x]
                    if is_guillotine(left_rects, bx, by, x, ey) and is_guillotine(right_rects, x, by, ex, ey):
                        return True

            # Try horizontal cuts.
            for y in range(by + 1, ey):
                if all((r[3] <= y or r[1] >= y) for r in rects):
                    bottom_rects = [r for r in rects if r[3] <= y]
                    top_rects = [r for r in rects if r[1] >= y]
                    if is_guillotine(bottom_rects, bx, by, ex, y) and is_guillotine(top_rects, bx, y, ex, ey):
                        return True

            return False

        computed_value = 0
        type_counts = [0] * m  # Count pieces for each type.
        rects = []  # To store placed rectangles as (x1, y1, x2, y2)

        # Process and validate each placement.
        for idx, placement in enumerate(placements):
            if not (isinstance(placement, (list, tuple)) and len(placement) == 6):
                raise ValueError(f"Placement {idx} is not a 6-tuple: {placement}")

            try:
                type_idx = int(placement[0])
                x = int(placement[1])
                y = int(placement[2])
                placed_len = int(placement[3])
                placed_wid = int(placement[4])
                orient = int(placement[5])
            except Exception:
                raise ValueError(f"Non-integer value in placement {idx}: {placement}")

            # Validate piece type index (using 1-indexing).
            if type_idx < 1 or type_idx > m:
                raise ValueError(f"Placement {idx} has invalid piece type index {type_idx}")

            # Orientation must be 0 (rotation is not allowed).
            if orient != 0:
                raise ValueError(f"Placement {idx} has invalid orientation flag {orient}; rotation is not allowed.")

            # Retrieve expected dimensions and value.
            piece = piece_types[type_idx - 1]
            p_length = piece['length']
            p_width = piece['width']
            max_allowed = piece['max']
            p_value = piece['value']

            # Since rotation is not allowed, expected dimensions are as given.
            expected_length, expected_width = p_length, p_width

            # Check that the placed dimensions match the expected dimensions.
            if placed_len != expected_length or placed_wid != expected_width:
                raise ValueError(
                    f"Placement {idx} dimensions ({placed_len}, {placed_wid}) do not match expected ({expected_length}, {expected_width})")

            # Check boundaries: the entire piece must lie within the stock sheet.
            if x < 0 or y < 0 or (x + placed_len) > stock_length or (y + placed_wid) > stock_width:
                raise ValueError(
                    f"Placement {idx} with rectangle {(x, y, x + placed_len, y + placed_wid)} is out of stock bounds (0,0) to ({stock_length},{stock_width})")

            # Passed validations: count the piece and add its value.
            type_counts[type_idx - 1] += 1
            computed_value += p_value

            # Record rectangle (bottom-left: (x, y), top-right: (x+placed_len, y+placed_wid))
            rects.append((x, y, x + placed_len, y + placed_wid))

        # Check for overlapping placements.
        num_rects = len(rects)
        for i in range(num_rects):
            for j in range(i + 1, num_rects):
                r1 = rects[i]
                r2 = rects[j]
                dx = min(r1[2], r2[2]) - max(r1[0], r2[0])
                dy = min(r1[3], r2[3]) - max(r1[1], r2[1])
                if dx > 0 and dy > 0:
                    raise ValueError(f"Placements {i} and {j} overlap.")

        # Check that no piece type is placed more times than its allowed maximum.
        for i in range(m):
            if type_counts[i] > piece_types[i]['max']:
                raise ValueError(
                    f"Piece type {i + 1} exceeds allowed count: {type_counts[i]} > {piece_types[i]['max']}")

        # Check the guillotine condition on the entire stock sheet.
        if not is_guillotine(rects, 0, 0, stock_length, stock_width):
            raise ValueError("Guillotine condition violated: the placement layout is not guillotine separable.")

        # Verify that the reported total_value matches the computed total.
        if computed_value != total_value:
            raise ValueError(f"Reported total value {total_value} does not match computed value {computed_value}.")

        return computed_value

    def norm_score(self, results):
        optimal_scores = {
            "cgcut1.txt": [244],
            "cgcut2.txt": [2892],
            "cgcut3.txt": [1860],
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

    def get_dev(self):
        dev = {'cgcut1.txt': [], 'cgcut2.txt': [], 'cgcut3.txt': []}

        return dev

