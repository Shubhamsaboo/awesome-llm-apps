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
from llm4ad.task.optimization.co_bench.assortment_problem_co_bench.template import template_program, task_description

__all__ = ['AssortPEvaluationCB']


class AssortPEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Assortment problem")
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
                    result = eva(j['m'], j['stocks'], j['pieces'])
                    fitness = self.eval_func(j['m'], j['n'], j['waste_cost'], j['stocks'], j['pieces'], result['objective'], result['placements'])
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Loads the input data for one or more cases from a TXT file.
        The file format is as follows for each case:
          1. A line with three tokens: m n waste_cost
             - m: number of piece types (int)
             - n: number of stock rectangles (int)
             - waste_cost: cost per unit area of waste (float)
          2. Next n lines: each with "length width fixed_cost" for a stock rectangle.
          3. Next m lines: each with "length width min max value" for a piece.
        If the file contains multiple cases, they should be separated by at least one blank line.
        Returns:
          A list of dictionaries, one per case. Each dictionary contains:
            - "m": int
            - "n": int
            - "waste_cost": float
            - "stocks": list of dicts (each with keys 'length', 'width', 'fixed_cost')
            - "pieces": list of dicts (each with keys 'length', 'width', 'min', 'max', 'value')
        """

        cases = []
        lines = [line.strip() for line in input_string.split('\n') if line.strip() != '']

        ptr = 0
        while ptr < len(lines):
            # Parse first line of a case.
            try:
                m_str, n_str, waste_cost_str = lines[ptr].split()
                m = int(m_str)
                n = int(n_str)
                waste_cost = float(waste_cost_str)
            except Exception:
                raise Exception("Error reading the case header (expected: m n waste_cost) at line {}".format(ptr + 1))
            ptr += 1

            stocks = []
            for i in range(n):
                if ptr >= len(lines):
                    raise Exception("Unexpected end of file while reading stocks.")
                tokens = lines[ptr].split()
                if len(tokens) != 3:
                    raise Exception("Invalid stock rectangle line at line {}: expected 3 tokens.".format(ptr + 1))
                try:
                    length, width, fixed_cost = float(tokens[0]), float(tokens[1]), float(tokens[2])
                except Exception:
                    raise Exception("Parsing error in stock rectangle at line {}.".format(ptr + 1))
                stocks.append({'length': length, 'width': width, 'fixed_cost': fixed_cost})
                ptr += 1

            pieces = []
            for j in range(m):
                if ptr >= len(lines):
                    raise Exception("Unexpected end of file while reading pieces.")
                tokens = lines[ptr].split()
                if len(tokens) != 5:
                    raise Exception("Invalid piece line at line {}: expected 5 tokens.".format(ptr + 1))
                try:
                    p_length = float(tokens[0])
                    p_width = float(tokens[1])
                    p_min = int(tokens[2])
                    p_max = int(tokens[3])
                    p_value = float(tokens[4])
                except Exception:
                    raise Exception("Parsing error in piece line at line {}.".format(ptr + 1))
                pieces.append({'length': p_length, 'width': p_width, 'min': p_min, 'max': p_max, 'value': p_value})
                ptr += 1

            cases.append({
                "m": m,
                "n": n,
                "waste_cost": waste_cost,
                "stocks": stocks,
                "pieces": pieces
            })
        return cases

    def eval_func(self, m, n, waste_cost, stocks, pieces, objective, placements):
        """
        Evaluates the solution for the arrangement optimization problem using waste area percentage as the metric.
        The overall waste area percentage is computed as:
             overall_waste_percentage = (total unused area) / (total stock area)
        where a lower percentage indicates better utilization. This metric disregards piece values and fixed costs.
        Infeasible solutions (due to piece count constraint violations or using more than 2 distinct stock types)
        will raise an exception.
        Inputs:
          - m (int): Number of piece types.
          - n (int): (Not used directly) originally denoted the number of stock rectangles, but now placements are stock instances.
          - waste_cost (float): Not used in this metric.
          - stocks (list of dict): Each dict represents a stock type with keys:
                'length', 'width', 'fixed_cost'.
                There is an infinite supply of each stock type.
          - pieces (list of dict): Each dict represents a piece type with keys:
                'length', 'width', 'min', 'max', 'value'.
          - placements (dict): Mapping from stock instance id (1-indexed) to a dictionary with keys:
                'stock_type' : (1-indexed id of the stock type used for this instance),
                'placements' : a list of placements for pieces within that stock instance.
                               Each placement is a dict with keys:
                                  'piece'       (piece type, 1-indexed),
                                  'x'           (x-coordinate of the bottom-left corner),
                                  'y'           (y-coordinate of the bottom-left corner),
                                  'orientation' (0 for normal, 1 for rotated 90°).
          - objective (float): Not used in this metric (provided for reference).
        Returns:
          The overall waste area percentage (float) if all constraints are satisfied.
        Raises:
          Exception: If a placement violates boundary or overlap conditions, if piece count constraints are not met,
                     or if more than 2 distinct stock types are used.
        """
        total_piece_counts = [0] * m
        total_stock_area = 0.0
        total_waste_area = 0.0
        used_stock_types = set()

        # Iterate over each stock instance in the placements.
        for stock_instance_id, instance_data in placements.items():
            # Validate the stock instance structure.
            if not isinstance(instance_data,
                              dict) or 'stock_type' not in instance_data or 'placements' not in instance_data:
                raise Exception(
                    f"Stock instance {stock_instance_id} is missing required keys ('stock_type', 'placements').")

            stock_type = instance_data['stock_type']
            # Check stock_type is valid.
            if not (1 <= stock_type <= len(stocks)):
                raise Exception(
                    f"Stock type {stock_type} in instance {stock_instance_id} is out of valid range (should be between 1 and {len(stocks)}).")
            used_stock_types.add(stock_type)

            # Retrieve stock type details and compute area.
            stock = stocks[stock_type - 1]
            stock_length, stock_width = stock['length'], stock['width']
            stock_area = stock_length * stock_width
            total_stock_area += stock_area

            used_area = 0.0
            placed_rectangles = []  # To check for overlaps within this stock instance.

            # Process each piece placement in this stock instance.
            for placement in instance_data['placements']:
                piece_type = placement.get('piece')
                x = placement.get('x')
                y = placement.get('y')
                orientation = placement.get('orientation')

                # Validate piece type.
                if not (1 <= piece_type <= m):
                    raise Exception(
                        f"Piece type {piece_type} in stock instance {stock_instance_id} is out of range (should be between 1 and {m}).")
                piece = pieces[piece_type - 1]

                # Determine dimensions based on orientation.
                if orientation == 0:
                    p_len, p_wid = piece['length'], piece['width']
                elif orientation == 1:
                    p_len, p_wid = piece['width'], piece['length']
                else:
                    raise Exception(
                        f"Invalid orientation {orientation} for piece type {piece_type} in stock instance {stock_instance_id}.")

                # Check that the piece lies fully within the stock boundaries.
                if x < 0 or y < 0 or (x + p_len) > stock_length + 1e-6 or (y + p_wid) > stock_width + 1e-6:
                    raise Exception(
                        f"Piece type {piece_type} in stock instance {stock_instance_id} is placed outside the stock boundaries.")

                # Check for overlapping pieces within the same stock instance.
                rect = (x, y, x + p_len, y + p_wid)
                for other in placed_rectangles:
                    if not (rect[2] <= other[0] or rect[0] >= other[2] or rect[3] <= other[1] or rect[1] >= other[3]):
                        raise Exception(f"Overlap detected in stock instance {stock_instance_id}.")
                placed_rectangles.append(rect)

                used_area += p_len * p_wid
                total_piece_counts[piece_type - 1] += 1

            total_waste_area += (stock_area - used_area)

        # Verify that no more than 2 distinct stock types were used.
        if len(used_stock_types) > 2:
            raise Exception(f"More than 2 distinct stock types used: found {len(used_stock_types)} types.")

        # Check piece count constraints for each piece type.
        for idx, piece in enumerate(pieces):
            count = total_piece_counts[idx]
            if count < piece['min'] or count > piece['max']:
                raise Exception(
                    f"Piece count violation for piece type {idx + 1}: count = {count}, required min = {piece['min']}, max = {piece['max']}."
                )

        if total_stock_area == 0:
            raise Exception("Total stock area is 0, invalid configuration.")

        overall_waste_percentage = total_waste_area / total_stock_area
        return overall_waste_percentage

    def norm_score(self, results):
        optimal_scores = {
            "assort1.txt": [7.69],
            "assort2.txt": [4.17],
            "assort3.txt": [5.87],
            "assort4.txt": [6.63],
            "assort5.txt": [4.95],
            "assort6.txt": [7.62],
            "assort7.txt": [16.84],
            "assort8.txt": [5.48],
            "assort9.txt": [9.07],
            "assort10.txt": [13.80],
            "assort11.txt": [6.65],
            "assort12.txt": [5.89],
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
                    normed_scores.append(optimal_list[idx] / score / 100)
                else:
                    normed_scores.append(score)
            normed[case] = (normed_scores, error_message)

        return normed

    def get_dev(self):
        dev = {'assort1.txt': [0], 'assort10.txt': [0], 'assort4.txt': [0],
               'assort7.txt': [0], }

        return dev

