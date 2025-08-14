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
from llm4ad.task.optimization.co_bench.bp_1d_co_bench.template import template_program, task_description

__all__ = ['BP1DEvaluationCB']


class BP1DEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Bin packing - one-dimensional")
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
                    result = eva(j['id'], j['bin_capacity'], j['num_items'], j['items'])
                    fitness = self.eval_func(j['id'], j['bin_capacity'], j['num_items'], j['best_known'], j['items'], result['nim_bins'], result['bins'])
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Load test cases from string content for the bin packing problem.
        The input format:
          1. The first nonempty line is an integer P, the number of test cases.
          2. For each test case:
             a. A line with the problem identifier (e.g., "u120_00").
             b. A line with three space-separated numbers: bin_capacity, num_items, best_known.
                (Note: bin_capacity and item sizes may be given as floats.)
             c. Then num_items lines, each with a number representing an item size.
        Returns:
          A list of dictionaries. Each dictionary contains the input data for one test case with keys:
            - 'id':           Problem identifier (string)
            - 'bin_capacity': Bin capacity (float)
            - 'num_items':    Number of items (int)
            - 'best_known':   Best known number of bins (int)
            - 'items':        List of item sizes (list of floats)
        """
        cases = []
        try:
            # Get all nonempty, stripped lines from string.
            in_lines = [line.strip() for line in input_string.split('\n') if line.strip() != '']
        except Exception as e:
            raise Exception("Error processing input string: " + str(e))

        if not in_lines:
            raise Exception("Input file is empty or improperly formatted.")

        try:
            num_cases = int(in_lines[0])
        except Exception as e:
            raise Exception("Error parsing the number of test cases: " + str(e))

        pos = 1
        for _ in range(num_cases):
            if pos >= len(in_lines):
                raise Exception("Unexpected end of file while reading a test case header.")
            # Read problem identifier.
            prob_id = in_lines[pos]
            pos += 1

            if pos >= len(in_lines):
                raise Exception(f"Missing header for problem {prob_id}.")
            header_parts = in_lines[pos].split()
            pos += 1
            if len(header_parts) < 3:
                raise Exception(
                    f"Header for problem {prob_id} must contain bin capacity, number of items, and best known bins.")
            try:
                # Use float for bin_capacity since it might be provided as a float.
                bin_capacity = float(header_parts[0])
                num_items = int(header_parts[1])
                best_known = int(header_parts[2])
            except Exception as e:
                raise Exception(f"Error parsing header for problem {prob_id}: {e}")

            items = []
            for i in range(num_items):
                if pos >= len(in_lines):
                    raise Exception(f"Unexpected end of file while reading items for problem {prob_id}.")
                try:
                    # Parse item sizes as floats.
                    item_size = float(in_lines[pos])
                except Exception as e:
                    raise Exception(f"Error parsing item size for problem {prob_id} at line {pos + 1}: {e}")
                items.append(item_size)
                pos += 1

            cases.append({
                'id': prob_id,
                'bin_capacity': bin_capacity,
                'num_items': num_items,
                'best_known': best_known,
                'items': items
            })

        return cases

    def eval_func(self, id, bin_capacity, num_items, best_known, items, num_bins, bins):
        """
        Evaluate the bin packing solution for a single test case.
        Parameters (from the input case and the solution):
          - id:           Problem identifier (string)
          - bin_capacity: Bin capacity (int)
          - num_items:    Number of items (int)
          - best_known:   Best known number of bins (int)
          - items:        List of item sizes (list of ints)
          - num_bins:     Number of bins used in the solution (int)
          - bins:         List of lists; each inner list contains 1-based item indices assigned to that bin.
        Returns:
          A scalar score (int). The score is the total number of bins used.
          If the solution is invalid (e.g., item indices are wrong, items not used exactly once, or bin capacity exceeded),
          a penalty of 1,000,000 is added to the score.
        """
        penalty = 1_000_000
        score = num_bins  # start with the number of bins used
        valid = True
        details = []

        # Check that the number of bin assignments matches num_bins.
        if len(bins) != num_bins:
            valid = False
            details.append("Declared number of bins does not match the number of bin assignments provided.")

        # Check each bin for capacity and valid item indices.
        # Also count item appearances.
        item_counts = [0] * (num_items + 1)  # index 0 unused
        for bin_index, bin_items in enumerate(bins, start=1):
            bin_total = 0
            for item_idx in bin_items:
                if item_idx < 1 or item_idx > num_items:
                    valid = False
                    details.append(f"Bin {bin_index} contains an invalid item index: {item_idx}.")
                    continue
                bin_total += items[item_idx - 1]
                item_counts[item_idx] += 1
            if bin_total > bin_capacity:
                valid = False
                details.append(f"Bin {bin_index} exceeds capacity: total size {bin_total} > capacity {bin_capacity}.")

        # Check that every item appears exactly once.
        for i in range(1, num_items + 1):
            if item_counts[i] != 1:
                valid = False
                details.append(f"Item {i} appears {item_counts[i]} times (expected exactly once).")

        if not valid:
            score = None
        else:
            score = (score - best_known) / best_known

        # For debugging purposes, one might print or log details.
        # For now, we simply return the computed score.
        return score

    def get_dev(self):
        dev = {'binpack1.txt': [7, 5, 16, 9, 13], 'binpack2.txt': [1, 15, 16, 4, 18],
               'binpack3.txt': [10, 18, 0, 19, 14], 'binpack4.txt': [11, 3, 16, 18, 17],
               'binpack5.txt': [10, 13, 0, 11, 17], 'binpack6.txt': [18, 11, 0, 6, 2],
               'binpack7.txt': [12, 17, 9, 15, 13], 'binpack8.txt': [4, 11, 19, 6, 17]}

        return dev
