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
from llm4ad.task.optimization.co_bench.equitable_partitioning_problem_co_bench.template import template_program, task_description

__all__ = ['EPPEvaluationCB']


class EPPEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Equitable partitioning problem")
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
                    result = eva(j['data'])
                    fitness = self.eval_func(data=j['data'], assignment=result['assignment'])
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Reads input string content where each non-empty line represents an individual with space-separated binary attributes.
        In case the input string contains multiple cases (separated by one or more blank lines), this function will
        separate them into distinct cases.
        Parameters:
            input_string (str): The string content with the input data.
        Returns:
            list: A list of dictionaries. Each dictionary represents one case with the key 'data' mapping to a 2D list
                  (matrix) of binary attributes (0 or 1). For example:
                  [
                      {"data": [[0, 1, 0], [1, 0, 1], ...]},
                      {"data": [[1, 1], [0, 1], ...]},
                      ...
                  ]
        Raises:
            Exception: If the string cannot be read, or if any line is invalid, contains non-integer tokens,
                       tokens not in {0, 1}, or if any row has an inconsistent number of attributes.
        """
        try:
            all_lines = [line.strip() for line in input_string.split('\n')]
        except Exception as e:
            raise Exception("Error reading input string: " + str(e))

        cases = []
        current_case = []
        for line_no, line in enumerate(all_lines, start=1):
            stripped = line.strip()
            # A blank line indicates a separator between cases.
            if not stripped:
                if current_case:
                    cases.append(current_case)
                    current_case = []
                continue
            current_case.append(stripped)

        # Add last case if file did not end with a blank line.
        if current_case:
            cases.append(current_case)

        # Parse each case into a data matrix.
        list_of_cases = []
        for case_idx, case_lines in enumerate(cases, start=1):
            matrix = []
            n_attributes = None
            for line_no, line in enumerate(case_lines, start=1):
                tokens = line.split()
                if not tokens:
                    raise Exception(f"Case {case_idx}, line {line_no} is empty or invalid.")
                try:
                    row = [int(token) for token in tokens]
                except ValueError:
                    raise Exception(f"Non-integer value found in case {case_idx}, line {line_no}.")
                for token in row:
                    if token not in (0, 1):
                        raise Exception(
                            f"Invalid attribute value {token} found in case {case_idx}, line {line_no}; expected only 0 or 1.")
                if n_attributes is None:
                    n_attributes = len(row)
                elif len(row) != n_attributes:
                    raise Exception(f"Inconsistent number of attributes in case {case_idx}, line {line_no}.")
                matrix.append(row)
            list_of_cases.append({"data": matrix})

        if not list_of_cases:
            raise Exception("Input file is empty or contains no valid cases.")

        return list_of_cases

    def eval_func(self, **kwargs):
        """
        Evaluates a partitioning solution for the equitable distribution problem using the new imbalance metric.
        Expected Parameters (provided via kwargs):
          - data (list of list of int): A matrix of binary attributes for individuals.
          - assignment (list of int): A list of positive integers representing group assignments for each individual.
        Evaluation Metric:
          For each attribute (column), compute the number of 1's per group. Then, compute the mean of these counts.
          The imbalance for the attribute is defined as the average of the absolute differences between each group's count and the mean count.
          The final score is the sum of these imbalances over all attributes.
          (A lower score indicates a more balanced partitioning.)
        Returns:
          total_imbalance: The computed total imbalance (float).
        Raises:
          Exception: If any expected parameter is missing, if the assignment format is invalid, or if the number of groups is not 8.
        """
        # Retrieve input data and assignment from kwargs
        if 'data' not in kwargs or 'assignment' not in kwargs:
            raise Exception("Missing required input parameters 'data' and/or 'assignment'.")

        data = kwargs['data']
        assignment = kwargs['assignment']
        #
        n_individuals = len(data)
        if len(assignment) != n_individuals:
            raise Exception(f"Expected {n_individuals} group assignments but found {len(assignment)}.")

        n_attributes = len(data[0])
        for idx, row in enumerate(data, start=1):
            if len(row) != n_attributes:
                raise Exception(f"Inconsistent number of attributes in data at individual {idx}.")

        # Ensure all group assignments are positive integers.
        for idx, g in enumerate(assignment, start=1):
            if not isinstance(g, int) or g < 1:
                raise Exception(f"Invalid group assignment at position {idx}: {g}. Must be a positive integer.")

        # Collect unique groups and check for exactly 8 groups.
        groups = set(assignment)
        if len(groups) != 8:
            raise Exception(f"Invalid number of groups: expected 8, but got {len(groups)}.")

        # Initialize per-group attribute sums.
        group_sums = {g: [0] * n_attributes for g in groups}
        for ind, group in enumerate(assignment):
            for j in range(n_attributes):
                group_sums[group][j] += data[ind][j]

        total_imbalance = 0.0
        for j in range(n_attributes):
            # Collect counts for attribute j from all groups
            attr_counts = [group_sums[g][j] for g in groups]
            mean_count = sum(attr_counts) / len(groups)
            # Compute average absolute difference from the mean
            # imbalance = sum(abs(count - mean_count) for count in attr_counts) / len(groups)
            imbalance = sum(abs(count - mean_count) for count in attr_counts)
            total_imbalance += imbalance

        return total_imbalance

    def norm_score(self, results):
        optimal_scores = {
            "eppperf1.txt": [0],
            "eppperf2.txt": [0],
            "eppperf3.txt": [0],
            "eppperf4.txt": [0],
            "eppperf5.txt": [0],
            "epprandom1.txt": [11.5],
            "epprandom2.txt": [12.75],
            "epprandom3.txt": [13.75],
            "epprandom4.txt": [14.50],
            "epprandom5.txt": [16.25],
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
                    if optimal_list[idx] == 0:
                        normed_scores.append((optimal_list[idx] + 1) / (score + 1))
                    else:
                        normed_scores.append(optimal_list[idx] / score)
                else:
                    normed_scores.append(score)
            normed[case] = (normed_scores, error_message)

        return normed

    def get_dev(self):
        dev = {'eppperf1.txt': [0], 'eppperf3.txt': [0],
               'epprandom2.txt': [0], 'epprandom4.txt': [0]}

        return dev



