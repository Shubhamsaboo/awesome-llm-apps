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
from llm4ad.task.optimization.co_bench.constrained_non_guillotine_cutting_co_bench.template import template_program, task_description

__all__ = ['CNCEvaluationCB']


class CNCEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Constrained non-guillotine cutting")
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
                    result = eva(j['stock_length'], j['stock_width'], j['pieces'])
                    fitness = self.eval_func(j['stock_length'], j['stock_width'], j['pieces'], result['placements'])
                    fitness_list.append(fitness)

            return np.mean(fitness_list)  # itself is a maximize problem

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Loads input data from a text file and returns a list of test case dictionaries.
        The input format:
          - First line: integer T (number of test cases)
          - For each test case:
              * A line with integer m (number of pieces)
              * A line with two integers: stock_length and stock_width
              * m subsequent lines, each with 5 integers:
                    length, width, min_required, max_allowed, value
        Returns:
          List[Dict]: A list where each element is a dictionary with keys:
              'stock_length': int,
              'stock_width': int,
              'pieces': list of dicts, each dict has:
                    'length': int,
                    'width': int,
                    'min': int,
                    'max': int,
                    'value': int
        """
        test_cases = []
        all_lines = [line.strip() for line in input_string.split('\n')]

        idx = 0
        T = int(all_lines[idx])
        idx += 1
        for _ in range(T):
            if idx >= len(all_lines):
                raise ValueError("Insufficient data for the expected number of test cases.")
            m = int(all_lines[idx])
            idx += 1

            stock_dims = list(map(int, all_lines[idx].split()))
            if len(stock_dims) != 2:
                raise ValueError("Invalid stock dimensions format.")
            stock_length, stock_width = stock_dims
            idx += 1

            pieces = []
            for _ in range(m):
                piece_data = list(map(int, all_lines[idx].split()))
                if len(piece_data) != 5:
                    raise ValueError("Invalid piece data format.")
                pieces.append({
                    'length': piece_data[0],
                    'width': piece_data[1],
                    'min': piece_data[2],
                    'max': piece_data[3],
                    'value': piece_data[4]
                })
                idx += 1

            test_cases.append({
                'stock_length': stock_length,
                'stock_width': stock_width,
                'pieces': pieces
            })

        return test_cases

    def eval_func(self, stock_length, stock_width, pieces, placements):
        """
        Evaluates the solution for a single test case.
        Parameters:
          - stock_length (int): Length of the stock rectangle.
          - stock_width (int): Width of the stock rectangle.
          - pieces (list of dict): List of piece definitions.
          - placements (list): List of placements; each placement is a 4-tuple:
                               (piece_type, x, y, r)
        Returns:
          float: The overall score, computed as the sum of values of all placed pieces,
                 if the solution is feasible.
        Raises:
          ValueError: If any constraint is violated.
        """
        counts = [0] * len(pieces)
        rects = []  # Each rectangle is represented as (x1, y1, x2, y2)

        for idx, placement in enumerate(placements):
            if not (isinstance(placement, (list, tuple)) and len(placement) == 4):
                raise ValueError(f"Placement at index {idx} is invalid; must be a 4-tuple.")

            piece_type, x, y, r = placement

            # Ensure that placement values are integers.
            if not all(isinstance(val, int) for val in (piece_type, x, y, r)):
                raise ValueError(f"All values in placement at index {idx} must be integers.")

            # Check piece_type validity.
            if piece_type < 1 or piece_type > len(pieces):
                raise ValueError(f"Placement at index {idx} has an invalid piece_type {piece_type}.")

            piece = pieces[piece_type - 1]

            # Determine dimensions based on rotation flag.
            if r == 0:
                p_len = piece['length']
                p_wid = piece['width']
            elif r == 1:
                p_len = piece['width']
                p_wid = piece['length']
            else:
                raise ValueError(f"Placement at index {idx} has an invalid rotation flag {r}.")

            # Check that the piece is fully within the stock boundaries.
            if x < 0 or y < 0 or (x + p_len) > stock_length or (y + p_wid) > stock_width:
                raise ValueError(f"Placement at index {idx} is out of stock boundaries.")

            # Record the rectangle: (x1, y1, x2, y2)
            rects.append((x, y, x + p_len, y + p_wid))
            counts[piece_type - 1] += 1

        # Check for overlapping placements.
        n = len(rects)
        for i in range(n):
            for j in range(i + 1, n):
                a = rects[i]
                b = rects[j]
                # Two rectangles do not overlap if one is completely to the left,
                # right, above, or below the other.
                if not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]):
                    raise ValueError(f"Placements at indices {i} and {j} overlap.")

        # Check that the count of placements for each piece type meets its constraints.
        for i, piece in enumerate(pieces):
            if counts[i] < piece['min'] or counts[i] > piece['max']:
                raise ValueError(f"Piece type {i + 1} count {counts[i]} does not meet constraints "
                                 f"[min: {piece['min']}, max: {piece['max']}].")

        # Compute the total score.
        total_score = 0
        for placement in placements:
            piece_type, x, y, r = placement
            piece = pieces[piece_type - 1]
            total_score += piece['value']

        return total_score

    def norm_score(self, results):
        optimal_scores = {
            "ngcutap.txt": [164, 230, 247, 268, 358, 289, 430, 834, 924, 1452, 1688, 1865, 1178, 1270, 2726, 1860,
                            27718,
                            22502, 24019, 32893, 27923],
            "ngcutcon.txt": [164, 230, 247, 268, 358, 289, 430, 834, 924, 1452, 1688, 1865, 1178, 1270, 2726, 1860,
                             27718,
                             22502, 24019, 32893, 27923],
            "ngcutfs1.txt": [30000] * 210,
            "ngcutfs2.txt": [30000] * 210,
            "ngcutfs3.txt": [30000] * 210,
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
        dev = {'ngcutap.txt': [19, 4, 12, 2, 8], 'ngcutcon.txt': [0, 8, 19, 7, 17],
               'ngcutfs1.txt': [51, 66, 120, 62, 8, 185, 197, 0, 170, 119, 103, 161, 173, 26, 153, 96, 13, 136, 5, 44,
                                150,
                                82, 86, 14, 71, 207, 135, 75, 97, 139, 118, 46, 108, 93, 99, 140, 204, 147, 16, 183, 27,
                                191, 176, 49, 127, 78, 10, 113, 110, 143, 199, 142, 167, 22, 50, 30, 180, 188, 154, 123,
                                63,
                                72, 203, 61, 28, 186, 159, 134, 19, 52, 39, 79, 98, 55, 56, 137, 148, 155, 163, 124,
                                174,
                                33, 1, 125, 77, 58, 151, 76, 116, 206, 156, 184, 12, 32, 53, 92, 164, 131, 175, 187,
                                157,
                                45, 201, 189, 54],
               'ngcutfs2.txt': [123, 108, 114, 43, 151, 116, 197, 23, 45, 166, 8, 126, 147, 87, 154, 12, 172, 103, 133,
                                143,
                                122, 68, 24, 97, 144, 179, 195, 52, 67, 1, 14, 167, 33, 65, 196, 46, 202, 206, 54, 63,
                                160,
                                159, 176, 79, 129, 61, 9, 164, 72, 115, 21, 111, 96, 66, 198, 104, 201, 92, 105, 125,
                                91,
                                119, 124, 94, 84, 20, 113, 203, 177, 15, 135, 120, 49, 194, 192, 98, 88, 158, 36, 171,
                                29,
                                199, 109, 185, 148, 130, 204, 70, 174, 207, 53, 142, 2, 89, 35, 51, 117, 145, 73, 10,
                                81,
                                83, 139, 4, 128],
               'ngcutfs3.txt': [193, 73, 128, 170, 197, 26, 85, 58, 105, 100, 36, 93, 32, 72, 110, 80, 16, 106, 160, 11,
                                129, 3, 89, 66, 87, 61, 27, 47, 171, 52, 176, 24, 203, 205, 186, 161, 135, 114, 200, 90,
                                124, 198, 141, 70, 14, 183, 81, 8, 86, 178, 54, 157, 25, 208, 38, 134, 39, 88, 111, 23,
                                190,
                                109, 152, 43, 98, 99, 163, 148, 201, 44, 192, 130, 30, 138, 33, 9, 209, 194, 4, 15, 37,
                                169,
                                188, 112, 123, 115, 173, 181, 108, 97, 133, 96, 53, 13, 48, 158, 71, 19, 149, 64, 74,
                                103,
                                102, 206, 143]}

        return dev

