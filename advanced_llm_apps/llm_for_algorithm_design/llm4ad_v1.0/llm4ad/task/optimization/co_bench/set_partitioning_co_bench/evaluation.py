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
from llm4ad.task.optimization.co_bench.set_partitioning_co_bench.template import template_program, task_description

__all__ = ['SPEvaluationCB']


class SPEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Set partitioning")
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
                    result = eva(j['num_rows'], j['num_columns'], j['columns_info'])
                    fitness = self.eval_func(num_rows=j['num_rows'], num_columns=j['num_columns'], columns_info=j['columns_info'], selected_columns=result['selected_columns'])
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Load and validate one or multiple set partitioning cases from a TXT file.
        The file may contain multiple cases. Each case is structured as follows:
          - The first non-empty line of a case contains two integers: num_rows and num_columns.
          - Then, for each of the num_columns columns, there is one line containing:
                cost (int), count (int), followed by exactly 'count' integers (the row indices covered).
        Each case is parsed and validated independently. If any inconsistency or formatting error is found,
        a ValueError is raised.
        Returns:
          cases (list): A list of dictionaries, each representing one case with keys:
                         - 'num_rows': int
                         - 'num_columns': int
                         - 'columns_info': dict mapping column index (1-indexed) -> (cost, set(row_indices))
        """
        cases = []
        lines = [line.strip() for line in input_string.split('\n') if line.strip() != '']

        index = 0
        total_lines = len(lines)

        while index < total_lines:
            # Parse header line for one case.
            header_tokens = lines[index].split()
            index += 1
            if len(header_tokens) < 2:
                raise ValueError("Header must contain two integers: num_rows and num_columns.")
            try:
                num_rows = int(header_tokens[0])
                num_columns = int(header_tokens[1])
            except Exception:
                raise ValueError("Header values must be integers.")

            columns_info = {}
            # There must be exactly num_columns lines following for the columns.
            for j in range(1, num_columns + 1):
                if index >= total_lines:
                    raise ValueError("Insufficient lines for all columns' data in a case.")
                parts = lines[index].split()
                index += 1

                if len(parts) < 2:
                    raise ValueError("Each column line must have at least 2 tokens (cost and count).")
                try:
                    cost = int(parts[0])
                    count = int(parts[1])
                except Exception:
                    raise ValueError("Column cost and count must be integers.")

                if len(parts) != 2 + count:
                    raise ValueError(f"Column {j} is expected to have {2 + count} tokens, but got {len(parts)}.")
                try:
                    row_list = [int(tok) for tok in parts[2:]]
                except Exception:
                    raise ValueError("Row indices must be integers.")

                for r in row_list:
                    if r < 1 or r > num_rows:
                        raise ValueError("Row index out of the valid range (1 to num_rows).")

                columns_info[j] = (cost, set(row_list))

            # Append the case as a dictionary.
            cases.append({
                "num_rows": num_rows,
                "num_columns": num_columns,
                "columns_info": columns_info
            })

        if not cases:
            raise ValueError("Input file is empty or contains no valid cases.")
        return cases

    def eval_func(self, **kwargs):
        """
        Evaluate a solution for a set partitioning problem case.
        Expected kwargs:
          - num_rows (int): Total number of rows.
          - num_columns (int): Total number of columns.
          - columns_info (dict): Dictionary mapping column index (1-indexed) to a tuple (cost, set(row indices)).
          - selected_columns (list): List of selected column indices (should be in strictly increasing order).
        Raises:
          ValueError: If any constraints are violated, such as an invalid output format,
                      a column index error, or if any row is not covered exactly once.
        Returns:
          score (int): The computed score, which is the total cost of the selected columns.
                       Lower scores are better.
        """
        # Retrieve input data.
        num_rows = kwargs["num_rows"]
        num_columns = kwargs["num_columns"]
        columns_info = kwargs["columns_info"]
        selected_columns = kwargs.get("selected_columns")

        # Validate that selected_columns is provided and is a list.
        if selected_columns is None or not isinstance(selected_columns, list):
            raise ValueError("selected_columns must be provided as a list.")

        # Enforce that the list is in strictly increasing order and has no duplicates.
        if selected_columns != sorted(selected_columns) or len(selected_columns) != len(set(selected_columns)):
            raise ValueError("selected_columns must be in strictly increasing order with no duplicates.")

        # Validate each selected column index.
        for col in selected_columns:
            if not isinstance(col, int) or col < 1 or col > num_columns:
                raise ValueError(f"Invalid column index: {col}. Must be an integer between 1 and {num_columns}.")

        total_cost = 0
        row_coverage = [0] * (num_rows + 1)  # 1-indexed; index 0 is unused.

        # Process each selected column.
        for col in selected_columns:
            if col not in columns_info:
                raise ValueError(f"Column {col} not found in columns_info.")
            cost, covered_rows = columns_info[col]
            total_cost += cost
            for r in covered_rows:
                if r < 1 or r > num_rows:
                    raise ValueError(f"Invalid row index: {r} (must be between 1 and {num_rows}).")
                row_coverage[r] += 1

        # Ensure that every row is covered exactly once.
        for r in range(1, num_rows + 1):
            if row_coverage[r] != 1:
                raise ValueError(f"Row {r} is covered {row_coverage[r]} times; each row must be covered exactly once.")

        return total_cost

    def norm_score(self, results):
        optimal_scores = {
            "bills_snowflake.txt": [34],
            "exotic_fives.txt": [12],
            "sppaa02.txt": [30494],
            "sppaa03.txt": [49649],
            "sppaa05.txt": [53839],
            "sppaa06.txt": [27040],
            "delta.txt": [126],
            "heart.txt": [180],
            "sppkl01.txt": [1086],
            "sppkl02.txt": [219],
            "meteor.txt": [60],
            "sppnw01.txt": [114852],
            "sppnw02.txt": [105444],
            "sppnw03.txt": [24492],
            "sppnw04.txt": [16862],
            "sppnw05.txt": [132878],
            "sppnw06.txt": [7810],
            "sppnw07.txt": [5476],
            "sppnw08.txt": [35894],
            "sppnw09.txt": [67760],
            "sppnw10.txt": [68271],
            "sppnw11.txt": [116256],
            "sppnw12.txt": [14118],
            "sppnw13.txt": [50146],
            "sppnw14.txt": [61844],
            "sppnw15.txt": [67743],
            "sppnw16.txt": [1181590],
            "sppnw17.txt": [11115],
            "sppnw18.txt": [340160],
            "sppnw19.txt": [10898],
            "sppnw20.txt": [16812],
            "sppnw21.txt": [7408],
            "sppnw22.txt": [6984],
            "sppnw23.txt": [12534],
            "sppnw24.txt": [6314],
            "sppnw25.txt": [5960],
            "sppnw26.txt": [6796],
            "sppnw27.txt": [9933],
            "sppnw28.txt": [8298],
            "sppnw29.txt": [4274],
            "sppnw30.txt": [3942],
            "sppnw31.txt": [8038],
            "sppnw32.txt": [14877],
            "sppnw33.txt": [6678],
            "sppnw34.txt": [10488],
            "sppnw35.txt": [7216],
            "sppnw36.txt": [7314],
            "sppnw37.txt": [10068],
            "sppnw38.txt": [5558],
            "sppnw39.txt": [10080],
            "sppnw40.txt": [10809],
            "sppnw41.txt": [11307],
            "sppnw42.txt": [7656],
            "sppnw43.txt": [8904],
            "sppus01.txt": [10036],
            "sppus02.txt": [5965],
            "sppus03.txt": [5338],
            "sppus04.txt": [17854],
            "sppaa01.txt": [55535.4],
            "sppaa04.txt": [25877.6],

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
                    normed_scores.append(optimal_list[idx] / score)
                else:
                    normed_scores.append(score)
            normed[case] = (normed_scores, error_message)

        return normed

    def get_dev(self):
        dev = {'bills_snowflake.txt': [0], 'meteor.txt': [0],
               'sppaa02.txt': [0], 'sppaa04.txt': [0], 'sppaa05.txt': [0],

               'sppkl02.txt': [0],
               'sppnw02.txt': [0],
               'sppnw04.txt': [0], 'sppnw06.txt': [0],
               'sppnw08.txt': [0], 'sppnw10.txt': [0], 'sppnw12.txt': [0],
               'sppnw14.txt': [0], 'sppnw16.txt': [0],
               'sppnw18.txt': [0], 'sppnw20.txt': [0], 'sppnw22.txt': [0],
               'sppnw24.txt': [0], 'sppnw26.txt': [0],
               'sppnw28.txt': [0], 'sppnw30.txt': [0], 'sppnw32.txt': [0],
               'sppnw34.txt': [0], 'sppnw36.txt': [0],
               'sppnw38.txt': [0], 'sppnw40.txt': [0], 'sppnw42.txt': [0],
               'sppus02.txt': [0], 'sppus04.txt': [0]}

        return dev







