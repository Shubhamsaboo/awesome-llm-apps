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
from llm4ad.task.optimization.co_bench.unconstrained_guillotine_cutting_co_bench.template import template_program, task_description

__all__ = ['UGCEvaluationCB']


class UGCEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Unconstrained guillotine cutting")
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
                    result = eva(j['m'], j['stock_width'], j['stock_height'], j['piece'], j['allow_rotation'])
                    fitness = self.eval_func(m=j['m'], stock_width=j['stock_width'], stock_height=j['stock_height'], pieces=j['piece'], placements=result['placements'])
                    fitness_list.append(fitness)

            return np.mean(fitness_list)  # itself is a maximize problem

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Loads one or more problem cases from the input file.
        The input is expected to contain one or more cases.
        Each case has the following format:
          - Line 1: An integer m (number of pieces).
          - Line 2: Two integers: stock_width and stock_height.
          - Next m lines: Each line contains three space-separated integers: l, w, value.
        Cases are concatenated one after the other (ignoring blank lines).
        Parameters:
            input_path (str): Path to the input file.
        Returns:
            list: A list of dictionaries. Each dictionary corresponds to one case and contains:
                - "m" (int): number of pieces.
                - "stock_width" (int): width of the stock rectangle.
                - "stock_height" (int): height of the stock rectangle.
                - "pieces" (dict): mapping from piece_id (1-indexed) to a dict with keys 'l', 'w', 'value'.
        """
        lines = [line.strip() for line in input_string.split('\n') if line.strip() != '']

        cases = []
        idx = 0
        total_lines = len(lines)
        while idx < total_lines:
            # Read the number of pieces for the current case.
            try:
                m = int(lines[idx])
            except Exception:
                raise ValueError(f"Invalid number of pieces at line {idx + 1}")
            idx += 1

            if idx >= total_lines:
                raise ValueError("Missing stock dimensions for a case.")

            # Read stock rectangle dimensions.
            stock_parts = lines[idx].split()
            if len(stock_parts) != 2:
                raise ValueError(f"Stock dimensions must consist of two integers at line {idx + 1}")
            try:
                stock_width, stock_height = map(int, stock_parts)
            except Exception:
                raise ValueError(f"Stock dimensions must be integers at line {idx + 1}")
            idx += 1

            # Read m piece specifications.
            pieces = {}
            for i in range(m):
                if idx >= total_lines:
                    raise ValueError(f"Not enough piece specifications for case starting at line {idx + 1}")
                parts = lines[idx].split()
                if len(parts) < 3:
                    raise ValueError(f"Piece {i + 1} specification is incomplete at line {idx + 1}")
                try:
                    l, w, value = map(int, parts[:3])
                except Exception:
                    raise ValueError(f"Piece {i + 1} contains non-integer data at line {idx + 1}")
                pieces[i + 1] = {'l': l, 'w': w, 'value': value}
                idx += 1

            case = {
                "m": m,
                "stock_width": stock_width,
                "stock_height": stock_height,
                "pieces": pieces,
                "allow_rotation": False,  # Default value since we can't determine from string
            }
            cases.append(case)

        return cases

    def eval_func(self, **kwargs):
        """
        Evaluates a candidate solution for the guillotine cutting problem.
        This function computes the total value of the placed pieces while enforcing
        the following constraints by raising errors when violated:
          1. Each placement must be entirely within the stock rectangle.
          2. Placements must not overlap.
          3. Each piece may be used at most once.
          4. Each placement must have a valid orientation (0 or 1).
        Parameters (passed as keyword arguments):
            - m (int): Number of pieces.
            - stock_width (int): Width of the stock rectangle.
            - stock_height (int): Height of the stock rectangle.
            - pieces (dict): Dictionary mapping piece_id to {'l', 'w', 'value'}.
            - placements (list): List of placements, where each placement is a dict with keys:
                  'piece_id', 'x', 'y', 'orientation'.
        Returns:
            float: Total value of the placed pieces if all constraints are met.
        Raises:
            ValueError: If any of the constraints (format, boundary, overlap, duplicate usage, or orientation)
                        are violated.
        """
        try:
            m = kwargs["m"]
            stock_width = kwargs["stock_width"]
            stock_height = kwargs["stock_height"]
            pieces = kwargs["pieces"]
            placements = kwargs.get("placements", [])
        except KeyError as e:
            raise ValueError(f"Missing required input parameter: {e}")

        total_value = 0.0
        used_piece_ids = set()
        rects = []

        # Process each placement.
        for placement in placements:
            try:
                piece_id = int(placement["piece_id"])
                x = int(placement["x"])
                y = int(placement["y"])
                orientation = int(placement["orientation"])
            except Exception as e:
                raise ValueError(f"Invalid placement format: {placement}. Error: {e}")

            if piece_id not in pieces:
                raise ValueError(f"Piece id {piece_id} not found in pieces.")

            # Check for duplicate usage.
            if piece_id in used_piece_ids:
                raise ValueError(f"Duplicate usage of piece id {piece_id}.")
            used_piece_ids.add(piece_id)

            # Check orientation.
            if orientation not in (0, 1):
                raise ValueError(f"Invalid orientation {orientation} for piece id {piece_id}; must be 0 or 1.")

            # Determine effective dimensions based on orientation.
            if orientation == 0:
                p_width = pieces[piece_id]['l']
                p_height = pieces[piece_id]['w']
            else:
                p_width = pieces[piece_id]['w']
                p_height = pieces[piece_id]['l']

            # Check boundaries.
            if x < 0 or y < 0 or (x + p_width) > stock_width or (y + p_height) > stock_height:
                raise ValueError(f"Placement of piece id {piece_id} is out of stock boundaries.")

            total_value += pieces[piece_id]['value']

            # Record rectangle for later overlap checks.
            rects.append({
                "x": x,
                "y": y,
                "width": p_width,
                "height": p_height
            })

        # Helper function to compute overlapping area between two rectangles.
        def overlap_area(r1, r2):
            x_overlap = max(0, min(r1["x"] + r1["width"], r2["x"] + r2["width"]) - max(r1["x"], r2["x"]))
            y_overlap = max(0, min(r1["y"] + r1["height"], r2["y"] + r2["height"]) - max(r1["y"], r2["y"]))
            return x_overlap * y_overlap

        # Check for overlapping pieces.
        n_rects = len(rects)
        for i in range(n_rects):
            for j in range(i + 1, n_rects):
                if overlap_area(rects[i], rects[j]) > 0:
                    raise ValueError("Overlapping detected between placements.")

        return total_value

    def norm_score(self, results):
        optimal_scores = {
            "gcut1.txt": [56460],
            "gcut2.txt": [60536],
            "gcut3.txt": [61036],
            "gcut4.txt": [61698],
            "gcut5.txt": [246000],
            "gcut6.txt": [238998],
            "gcut7.txt": [242567],
            "gcut8.txt": [246633],
            "gcut9.txt": [971100],
            "gcut10.txt": [982025],
            "gcut11.txt": [980096],
            "gcut12.txt": [979986],
            "gcut13.txt": [8997780],
            "gcut1r.txt": [58136],
            "gcut2r.txt": [60611],
            "gcut3r.txt": [61626],
            "gcut4r.txt": [62265],
            "gcut5r.txt": [246000],
            "gcut6r.txt": [240951],
            "gcut7r.txt": [245866],
            "gcut8r.txt": [247787],
            "gcut9r.txt": [971100],
            "gcut10r.txt": [982025],
            "gcut11r.txt": [980096],
            "gcut12r.txt": [988694],
            "gcut13r.txt": [9000000],
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
        dev = {'gcut1.txt': [], 'gcut10r.txt': [], 'gcut11.txt': [],
               'gcut12r.txt': [], 'gcut13.txt': [], 'gcut2r.txt': [],
               'gcut3.txt': [], 'gcut4r.txt': [], 'gcut5.txt': [],
               'gcut6r.txt': [], 'gcut7r.txt': [], 'gcut8r.txt': [],
               'gcut9.txt': [], }

        return dev


