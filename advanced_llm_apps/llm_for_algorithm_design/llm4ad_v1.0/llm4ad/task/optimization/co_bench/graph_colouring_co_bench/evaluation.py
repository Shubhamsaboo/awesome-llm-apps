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
from llm4ad.task.optimization.co_bench.graph_colouring_co_bench.template import template_program, task_description

__all__ = ['GCEvaluationCB']


class GCEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Graph colouring")
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
                    result = eva(j['n'], j['edges'], j['adjacency'])
                    fitness = self.eval_func(n=j['n'], adjacency=j['adjacency'], result=result)
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Reads the input DIMACS string, which may contain one or more cases.
        Each case is separated by a header line (starting with "p"). For each case, the function:
          - Ignores blank lines and comment lines (starting with "c").
          - Parses the header line ("p edge <n> <m>") if present; if absent, determines n from edge listings.
          - Parses each edge line (starting with "e") to extract the edge (u,v).
          - Builds an adjacency list mapping each vertex (from 1 to n) to its adjacent vertices.
        Returns:
            A list where each element is a dictionary containing the data for one case.
            Each dictionary has at least the following keys:
                - 'n': int, number of vertices.
                - 'edges': list of (u, v) tuples.
                - 'adjacency': dict mapping vertex (1..n) to a set of adjacent vertices.
        """

        all_lines = [line.strip() for line in input_string.split('\n')]

        cases = []
        current_case_lines = []
        found_header = False

        # Separate file content into multiple cases based on header lines ("p ...")
        for line in all_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("c"):
                continue  # skip blank lines and comments
            if stripped.startswith("p"):
                # Start of a new case: if current_case_lines not empty, finish previous case.
                if current_case_lines:
                    cases.append(current_case_lines)
                    current_case_lines = []
                found_header = True
            current_case_lines.append(stripped)
        if current_case_lines:
            cases.append(current_case_lines)

        # If no header line was found in the entire file, treat entire file as one case.
        if not found_header and not cases:
            # Filter out blank lines and comments from all_lines and treat as single case.
            cases = [[line for line in all_lines if line.strip() and not line.strip().startswith("c")]]

        case_data_list = []
        # Process each case's lines.
        for case_lines in cases:
            n = None  # number of vertices
            edges = []
            vertices_found = set()

            for line in case_lines:
                parts = line.split()
                if parts[0] == "p":
                    # Expected format: p edge <n> <m>
                    if len(parts) < 4:
                        raise ValueError("Problem line malformed: " + line)
                    try:
                        n = int(parts[2])
                    except Exception as e:
                        raise ValueError("Error parsing problem line: " + str(e))
                elif parts[0] == "e":
                    # Expected format: e <u> <v>
                    if len(parts) < 3:
                        raise ValueError("Edge line malformed: " + line)
                    try:
                        u = int(parts[1])
                        v = int(parts[2])
                        edges.append((u, v))
                        vertices_found.update([u, v])
                    except Exception as e:
                        raise ValueError("Error parsing edge line: " + str(e))
            # If n was not provided in the header, use the maximum vertex id found.
            if n is None:
                if vertices_found:
                    n = max(vertices_found)
                else:
                    raise ValueError("No vertex information found in input.")

            # Build adjacency list.
            adjacency = {i: set() for i in range(1, n + 1)}
            for (u, v) in edges:
                if u in adjacency:
                    adjacency[u].add(v)
                if v in adjacency:
                    adjacency[v].add(u)

            case_data_list.append({
                'n': n,
                'edges': edges,
                'adjacency': adjacency
            })

        return case_data_list

    def eval_func(self, **kwargs):
        """
        Evaluates a solution for a single case.
        Expected kwargs:
            - 'n': int, number of vertices.
            - 'adjacency': dict mapping each vertex (1..n) to a set of adjacent vertices.
            - Plus all key-value pairs from the solution dictionary produced by solve,
              mapping vertex ids to assigned positive integer colors.
        Evaluation:
            - Verifies that every vertex from 1 to n is assigned a positive integer color.
            - For each edge (u,v), if the assigned colors are the same, counts as a conflict.
            - Let C be the total number of conflicts and k be the number of distinct colors used.
            - If C > 0, the solution is invalid and an error is raised.
            - If C == 0, the score is simply k (lower is better).
        Returns:
            A scalar score (integer or float) representing the evaluation of the solution.
        """
        # Extract expected case data.
        try:
            n = kwargs['n']
            adjacency = kwargs['adjacency']
        except KeyError as e:
            raise KeyError("Missing required case data key: " + str(e))

        # The solution should include an assignment for every vertex (1..n).
        result = kwargs.get('result', {})
        solution = {k: v for k, v in result.items() if isinstance(k, int) or (isinstance(k, str) and k.isdigit())}
        # Normalize keys to integers.
        normalized_solution = {}
        for key, value in solution.items():
            try:
                vertex = int(key)
            except Exception:
                continue
            normalized_solution[vertex] = value

        expected_vertices = set(range(1, n + 1))
        if set(normalized_solution.keys()) != expected_vertices:
            raise ValueError("The solution must assign a color to every vertex from 1 to " + str(n))

        # Check that every color is a positive integer.
        for v, color in normalized_solution.items():
            if not (isinstance(color, int) and color >= 1):
                raise ValueError("Invalid color for vertex {}: {}. Colors must be positive integers.".format(v, color))

        # Count conflicts: for each edge, if both endpoints have the same color, count a conflict.
        conflict_count = 0
        for u in range(1, n + 1):
            for v in adjacency[u]:
                if u < v:  # count each edge only once
                    if normalized_solution[u] == normalized_solution[v]:
                        conflict_count += 1

        if conflict_count > 0:
            raise ValueError("Invalid coloring: {} conflict(s) found.".format(conflict_count))

        num_colors = len(set(normalized_solution.values()))
        score = num_colors

        return score

    def norm_score(self, results):
        optimal_scores = {
            "gcol1.txt": [15],
            "gcol10.txt": [15],
            "gcol11.txt": [15],
            "gcol12.txt": [15],
            "gcol13.txt": [15],
            "gcol14.txt": [15],
            "gcol15.txt": [15],
            "gcol16.txt": [15],
            "gcol17.txt": [15],
            "gcol18.txt": [15],
            "gcol19.txt": [15],
            "gcol2.txt": [15],
            "gcol20.txt": [15],
            "gcol21.txt": [34],
            "gcol22.txt": [34],
            "gcol23.txt": [34],
            "gcol24.txt": [34],
            "gcol25.txt": [34],
            "gcol26.txt": [34],
            "gcol27.txt": [34],
            "gcol28.txt": [34],
            "gcol29.txt": [34],
            "gcol3.txt": [15],
            "gcol30.txt": [34],
            "gcol4.txt": [15],
            "gcol5.txt": [15],
            "gcol6.txt": [15],
            "gcol7.txt": [15],
            "gcol8.txt": [15],
            "gcol9.txt": [15]
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
        dev = {'gcol1.txt': [0], 'gcol11.txt': [0], 'gcol13.txt': [0],
               'gcol15.txt': [0], 'gcol17.txt': [0], 'gcol19.txt': [0],
               'gcol21.txt': [0], 'gcol23.txt': [0], 'gcol25.txt': [0],
               'gcol27.txt': [0], 'gcol29.txt': [0], 'gcol3.txt': [0],
               'gcol5.txt': [0], 'gcol7.txt': [0], 'gcol9.txt': [0]}

        return dev




