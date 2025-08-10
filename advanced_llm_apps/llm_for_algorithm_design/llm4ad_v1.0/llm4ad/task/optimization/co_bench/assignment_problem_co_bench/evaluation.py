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
from llm4ad.task.optimization.co_bench.assignment_problem_co_bench.template import template_program, task_description

__all__ = ['APEvaluationCB']


class APEvaluationCB(Evaluation):
    """Evaluator for assignment problem."""

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Assignment problem")
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
                    result = eva(j['n'], j['cost_matrix'])
                    fitness = self.eval_func(n=j['n'], cost_matrix=j['cost_matrix'], total_cost=result['total_cost'], assignment=result['assignment'])
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Reads input string content and separates it into multiple cases for the assignment problem.
        The input is expected to contain one or more cases. Each case has the following format:
          - The first non-empty line of the case is a single integer n (the number of items/agents).
          - The remaining tokens in the case provide the cost information. This can be in one of two formats:
              1. Dense Format: Exactly n*n numeric tokens (row-major order).
              2. Sparse Format: A sequence of tokens in groups of three: (i, j, cost). Any (i,j)
                 not specified is assigned a cost equal to 1000 times the maximum provided cost in that row.
        Cases in the input are separated by one or more blank lines.
        Parameters:
          input_string (str): The input content as string.
        Returns:
          A list of dictionaries, each containing:
              - "n": int, the number of items.
              - "cost_matrix": numpy.ndarray of shape (n, n) with the assignment costs.
        """
        import math

        all_lines = [line.rstrip() for line in input_string.split('\n')]

        # Group lines into cases using blank lines as delimiters.
        cases = []
        current_block = []
        for line in all_lines:
            if line.strip() == "":
                if current_block:
                    cases.append(current_block)
                    current_block = []
            else:
                current_block.append(line.strip())
        if current_block:
            cases.append(current_block)

        case_list = []
        for block in cases:
            if not block:
                continue
            try:
                n = int(block[0])
            except Exception as e:
                raise ValueError("The first line of each case must be an integer representing n.") from e

            tokens = []
            for line in block[1:]:
                tokens.extend(line.split())

            # Determine the format.
            if len(tokens) == n * n:
                try:
                    numbers = [float(token) for token in tokens]
                except Exception as e:
                    raise ValueError("Non-numeric token found in dense format.") from e
                cost_matrix = np.array(numbers).reshape(n, n)
            elif len(tokens) % 3 == 0:
                cost_matrix = np.full((n, n), math.inf)
                for idx in range(0, len(tokens), 3):
                    try:
                        i = int(tokens[idx])
                        j = int(tokens[idx + 1])
                        cost = float(tokens[idx + 2])
                    except Exception as e:
                        raise ValueError("Invalid token encountered in sparse format.") from e
                    if not (1 <= i <= n and 1 <= j <= n):
                        raise ValueError(f"Indices out of range in sparse format: i={i}, j={j}.")
                    cost_matrix[i - 1][j - 1] = cost
                # Set unspecified assignments.
                for i in range(n):
                    if np.all(np.isinf(cost_matrix[i])):
                        raise ValueError(f"Row {i + 1} has no valid assignments.")
                    max_finite = np.max(cost_matrix[i][np.isfinite(cost_matrix[i])])
                    cost_matrix[i][np.isinf(cost_matrix[i])] = max_finite * 1000
            else:
                raise ValueError(
                    "Input case format not recognized. Expect either n*n tokens (dense) or a multiple of 3 tokens (sparse).")

            case_list.append({"n": n, "cost_matrix": cost_matrix})
        return case_list

    def eval_func(self, **kwargs):
        """
        Evaluates the solution of the Assignment Problem for a single case.
        Parameters:
          - case (dict): A dictionary containing the case data with keys:
                * "n": int, the number of items/agents.
                * "cost_matrix": numpy.ndarray, the cost matrix.
          - solution (dict): A dictionary representing the solution returned by solve(), with keys:
                * "total_cost": numeric, the total cost reported by the solution.
                * "assignment": list of tuples (i, j) where i is the item (1-indexed) and j is the assigned agent (1-indexed).
        Returns:
          A numeric score representing the total cost computed from the cost_matrix based on the provided assignment.
        The function performs the following checks:
          - Each item (1 to n) must be assigned exactly once.
          - Each agent (1 to n) must be assigned exactly once.
          - The computed total cost (from the cost_matrix and assignment) must match the reported total_cost
            (within a small tolerance). If not, the computed total is used.
        """
        import math

        n = kwargs.get("n")
        cost_matrix = kwargs.get("cost_matrix")

        # Validate the assignment.
        assignment = {}  # Maps item i to agent j.
        assigned_agents = set()
        if not isinstance(kwargs.get("assignment"), list):
            raise ValueError("Solution must include an 'assignment' list.")
        for idx, pair in enumerate(kwargs["assignment"], start=1):
            if not (isinstance(pair, (list, tuple)) and len(pair) == 2):
                raise ValueError(f"Assignment entry {idx} must be a tuple/list of two integers (i, j).")
            i_val, j_val = pair
            if i_val in assignment:
                raise ValueError(f"Duplicate assignment for item {i_val} found.")
            if j_val in assigned_agents:
                raise ValueError(f"Agent {j_val} assigned more than once.")
            if not (1 <= i_val <= n and 1 <= j_val <= n):
                raise ValueError(f"Assignment indices ({i_val}, {j_val}) are out of range (must be between 1 and {n}).")
            assignment[i_val] = j_val
            assigned_agents.add(j_val)

        if len(assignment) != n:
            raise ValueError(f"Incomplete assignment: expected {n} assignments, but got {len(assignment)}.")

        # Compute the total cost based on the assignment.
        computed_total = 0.0
        for i in range(1, n + 1):
            j_val = assignment[i]
            cost = cost_matrix[i - 1][j_val - 1]
            if cost == math.inf:
                raise ValueError(f"Assignment ({i}, {j_val}) has an infinite cost, hence invalid.")
            computed_total += cost

        return computed_total

    def norm_score(self, results):
        optimal_scores = {
            "assign100.txt": [305],
            "assign200.txt": [475],
            "assign300.txt": [626],
            "assign400.txt": [804],
            "assign500.txt": [991],
            "assign600.txt": [1176],
            "assign700.txt": [1362],
            "assign800.txt": [1552],
            "assignp800.txt": [2239],
            "assignp1500.txt": [5839],
            "assignp3000.txt": [18696],
            "assignp5000.txt": [48533],
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
        dev = {'assign100.txt': [0], 'assign400.txt': [0], 'assign700.txt': [0], 'assignp3000.txt': [0]}

        return dev
