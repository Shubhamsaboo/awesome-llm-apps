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
from llm4ad.task.optimization.co_bench.set_covering_co_bench.template import template_program, task_description

__all__ = ['SCEvaluationCB']


class SCEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Set covering")
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
                    result = eva(j['m'], j['n'], j['costs'], j['row_cover'])
                    fitness = self.eval_func(m=j['m'], n=j['n'], costs=j['costs'], row_cover=j['row_cover'], selected_columns=result['selected_columns'])
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Loads one or more set covering test cases from string content.
        The input can contain one or more cases. Each case must follow one of three formats:
          Format A (SCP/Beasley):
            - Header (first nonempty line): two integers, m and n.
            - Next: a cost vector of n integers (which may span multiple lines).
            - Then: for each row, a line that starts with an integer k (number of columns covering the row)
                    followed by k space‑separated 1-indexed column indices.
          Format B (Real-world rail problems):
            - Header: two integers, m and n.
            - Next n nonempty lines: each line describes a column by giving:
                  cost, the number of rows the column covers, and then that many 1-indexed row indices.
            - Row coverage is then built by aggregating the information from each column.
          Format C (Dense row format):
            - Header: two integers, m and n.
            - Next m nonempty lines: each line lists the 1-indexed column indices that cover that row.
            - In this format, every column has an implicit unit cost.
        If the input contains multiple cases, it is assumed that the cases are separated
        by at least one blank line.
        Returns:
          A list of cases, where each case is a dictionary with keys:
             - "m": number of rows (int)
             - "n": number of columns (int)
             - "costs": list of column costs (list of int)
             - "row_cover": list of lists; each inner list contains the 1-indexed column numbers covering that row.
        """
        import re

        content = input_string.strip()

        # Split into blocks by one or more blank lines.
        blocks = re.split(r'\n\s*\n', content)
        cases = []

        # Check if the very first block is simply a test-case count.
        first_block_tokens = blocks[0].split()
        if len(first_block_tokens) == 1:
            try:
                num_cases = int(first_block_tokens[0])
                # Remove the count block and treat the remaining blocks as cases.
                blocks = blocks[1:]
                if len(blocks) != num_cases:
                    # Fall back: if the number doesn't match, assume each block is a case.
                    pass
            except Exception:
                pass  # Not a test-case count; treat first block as a case.

        for block in blocks:
            case = self._parse_single_case(block)
            cases.append(case)
        return cases

    def _parse_single_case(self, block):
        """
        Helper function to parse a single test case from a block (string) of text.
        The block must have its lines (nonempty) in one of the three supported formats.
        """
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            raise ValueError("Encountered an empty test case block.")

        header = lines[0].split()
        if len(header) < 2:
            raise ValueError("Header must contain at least two integers (m and n).")
        try:
            m = int(header[0])
            n = int(header[1])
        except Exception as e:
            raise ValueError("Error parsing m and n from header: " + str(e))

        remaining_lines = lines[1:]

        # Determine format based on the number of remaining lines.
        if len(remaining_lines) == n:
            # Format B: one line per column.
            costs = []
            col_rows = []
            for j in range(n):
                tokens = remaining_lines[j].split()
                if len(tokens) < 2:
                    raise ValueError(f"Column {j + 1}: expected at least cost and count.")
                try:
                    cost = int(tokens[0])
                    count = int(tokens[1])
                except Exception as e:
                    raise ValueError(f"Error parsing cost/count for column {j + 1}: {e}")
                if len(tokens) < 2 + count:
                    raise ValueError(f"Column {j + 1}: expected {count} row indices, got {len(tokens) - 2}.")
                try:
                    rows_for_col = list(map(int, tokens[2:2 + count]))
                except Exception as e:
                    raise ValueError(f"Error parsing row indices for column {j + 1}: {e}")
                costs.append(cost)
                col_rows.append(rows_for_col)
            # Build row coverage from column data.
            row_cover = [[] for _ in range(m)]
            for j in range(n):
                for r in col_rows[j]:
                    if r < 1 or r > m:
                        raise ValueError(f"Column {j + 1}: row index {r} is out of bounds.")
                    row_cover[r - 1].append(j + 1)
            return {"m": m, "n": n, "costs": costs, "row_cover": row_cover}

        elif len(remaining_lines) == m:
            # Format C: one line per row (dense row format).
            costs = [1] * n
            row_cover = []
            for i in range(m):
                try:
                    cols = list(map(int, remaining_lines[i].split()))
                except Exception as e:
                    raise ValueError(f"Error parsing row {i + 1}: {e}")
                row_cover.append(cols)
            return {"m": m, "n": n, "costs": costs, "row_cover": row_cover}

        else:
            # Format A: SCP test case.
            # First, read cost vector tokens until we have n tokens.
            cost_tokens = []
            line_index = 0
            while line_index < len(remaining_lines) and len(cost_tokens) < n:
                tokens = remaining_lines[line_index].split()
                cost_tokens.extend(tokens)
                line_index += 1
            if len(cost_tokens) < n:
                raise ValueError("Not enough tokens for cost vector.")
            try:
                costs = list(map(int, cost_tokens[:n]))
            except Exception as e:
                raise ValueError("Error converting cost tokens to integers: " + str(e))

            # The remaining tokens represent row coverage.
            row_tokens = []
            for line in remaining_lines[line_index:]:
                row_tokens.extend(line.split())
            token_index = 0
            row_cover = []
            for i in range(m):
                if token_index >= len(row_tokens):
                    raise ValueError(f"Not enough tokens for row {i + 1}.")
                try:
                    k = int(row_tokens[token_index])
                except Exception as e:
                    raise ValueError(f"Error parsing coverage count for row {i + 1}: {e}")
                token_index += 1
                if token_index + k > len(row_tokens):
                    raise ValueError(f"Not enough tokens for row {i + 1}: expected {k} tokens.")
                try:
                    cols = list(map(int, row_tokens[token_index: token_index + k]))
                except Exception as e:
                    raise ValueError(f"Error parsing column indices for row {i + 1}: {e}")
                token_index += k
                row_cover.append(cols)
            return {"m": m, "n": n, "costs": costs, "row_cover": row_cover}

    def eval_func(self, **kwargs):
        """
        Evaluates the solution for a single test case.
        Parameters:
          - m: (int) number of rows.
          - n: (int) number of columns.
          - costs: (list of int) where costs[j] is the cost for column j+1.
          - row_cover: (list of list of int) where row_cover[i] contains the 1-indexed columns covering row i+1.
          - selected_columns: a list of chosen 1-indexed column numbers.
        Evaluation:
          1. Compute the total cost as the sum of the costs for each selected column.
          2. Verify that every row is covered by at least one of the selected columns.
             If any row is uncovered, the function raises an error indicating the constraint violation.
        Returns:
          A scalar value representing the computed score (total cost) if all constraints are met.
        Raises:
          KeyError: if "selected_columns" is not provided in kwargs.
          ValueError: if any selected column is out of valid bounds or if any row is left uncovered.
        """
        m = kwargs["m"]
        n = kwargs["n"]
        costs = kwargs["costs"]
        row_cover = kwargs["row_cover"]

        if "selected_columns" not in kwargs:
            raise KeyError("Solution must contain 'selected_columns'.")

        selected_columns = set(kwargs["selected_columns"])

        # Check that each selected column is within valid bounds.
        for col in selected_columns:
            if col < 1 or col > n:
                raise ValueError(f"Column {col} is out of bounds (should be between 1 and {n}).")

        computed_cost = sum(costs[col - 1] for col in selected_columns)

        # Verify that every row is covered by at least one selected column.
        uncovered_rows = []
        for i in range(m):
            if not set(row_cover[i]).intersection(selected_columns):
                uncovered_rows.append(i + 1)

        if uncovered_rows:
            raise ValueError("Infeasible solution: rows such as {} are not covered.".format(
                ', '.join(map(str, uncovered_rows[:10]))
            ))

        return computed_cost

    def norm_score(self, results):
        optimal_scores = {
            "scp41.txt": [429],
            "scp42.txt": [512],
            "scp43.txt": [516],
            "scp45.txt": [512],
            "scp47.txt": [430],
            "scp49.txt": [641],
            "scp410.txt": [514],
            "scp53.txt": [226],
            "scp55.txt": [211],
            "scp56.txt": [213],
            "scp58.txt": [288],
            "scp59.txt": [279],
            "scp510.txt": [265],
            "scp44.txt": [494],
            "scp46.txt": [560],
            "scp48.txt": [492],
            "scp51.txt": [253],
            "scp52.txt": [302],
            "scp54.txt": [242],
            "scp57.txt": [293],
            "scp61.txt": [138],
            "scp62.txt": [146],
            "scp63.txt": [145],
            "scp64.txt": [131],
            "scp65.txt": [161],
            "scpa1.txt": [253],
            "scpa2.txt": [252],
            "scpa3.txt": [232],
            "scpa4.txt": [234],
            "scpa5.txt": [236],
            "scpb1.txt": [69],
            "scpb2.txt": [76],
            "scpb3.txt": [80],
            "scpb4.txt": [79],
            "scpb5.txt": [72],
            "scpc1.txt": [227],
            "scpc2.txt": [219],
            "scpc3.txt": [243],
            "scpc4.txt": [219],
            "scpc5.txt": [215],
            "scpd1.txt": [60],
            "scpd2.txt": [66],
            "scpd3.txt": [72],
            "scpd4.txt": [62],
            "scpd5.txt": [61],
            "scpe1.txt": [5],
            "scpe2.txt": [5],
            "scpe3.txt": [5],
            "scpe4.txt": [5],
            "scpe5.txt": [5],
            "scpnre1.txt": [29],
            "scpnre2.txt": [32],
            "scpnre3.txt": [28],
            "scpnre4.txt": [30],
            "scpnre5.txt": [28],
            "scpnrf1.txt": [15],
            "scpnrf2.txt": [16],
            "scpnrf3.txt": [15],
            "scpnrf4.txt": [15],
            "scpnrf5.txt": [14],
            "scpnrg1.txt": [184],
            "scpnrg2.txt": [163],
            "scpnrg3.txt": [174],
            "scpnrg4.txt": [176],
            "scpnrg5.txt": [175],
            "scpnrh1.txt": [68],
            "scpnrh2.txt": [66],
            "scpnrh3.txt": [65],
            "scpnrh4.txt": [63],
            "scpnrh5.txt": [60],
            "scpcyc06.txt": [48.0],
            "scpcyc07.txt": [112.0],
            "scpcyc08.txt": [256.0],
            "scpcyc09.txt": [576.0],
            "scpcyc010.txt": [1280.0],
            "scpcyc011.txt": [2816.0],
            "scpclr10.txt": [21.0],
            "scpclr11.txt": [16.5],
            "scpclr12.txt": [16.5],
            "scpclr13.txt": [14.3],
            "rail507.txt": [172.4],
            "rail516.txt": [182],
            "rail582.txt": [209.5],
            "rail2536.txt": [691],
            "rail2586.txt": [936.1],
            "rail4284.txt": [1065],
            "rail4872.txt": [1509],
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
        dev = {'rail2536.txt': [0], 'rail4284.txt': [0],
               'rail516.txt': [0], 'rail582.txt': [0],
               'scp410.txt': [0], 'scp42.txt': [0],
               'scp44.txt': [0], 'scp48.txt': [0],
               'scp52.txt': [0], 'scp54.txt': [0],
               'scp56.txt': [0], 'scp58.txt': [0], 'scp62.txt': [0],
               'scp64.txt': [0], 'scpa2.txt': [0],
               'scpa4.txt': [0], 'scpb2.txt': [0], 'scpb4.txt': [0],
               'scpc2.txt': [0], 'scpc4.txt': [0],
               'scpclr10.txt': [0], 'scpclr12.txt': [0], 'scpcyc010.txt': [0],
               'scpcyc06.txt': [0], 'scpcyc08.txt': [0],
               'scpd2.txt': [0], 'scpd4.txt': [0], 'scpd5.txt': [0],
               'scpe2.txt': [0], 'scpe4.txt': [0], 'scpnre2.txt': [0],
               'scpnre4.txt': [0], 'scpnrf2.txt': [0],
               'scpnrf4.txt': [0], 'scpnrg2.txt': [0],
               'scpnrg4.txt': [0], 'scpnrh2.txt': [0],
               'scpnrh4.txt': [0]}

        return dev







