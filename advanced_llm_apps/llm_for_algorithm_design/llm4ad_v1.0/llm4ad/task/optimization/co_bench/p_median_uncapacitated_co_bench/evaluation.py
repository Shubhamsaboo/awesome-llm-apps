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
from llm4ad.task.optimization.co_bench.p_median_uncapacitated_co_bench.template import template_program, task_description

__all__ = ['PMUEvaluationCB']


class PMUEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "p-median - uncapacitated")
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
                    result = eva(j['n'], j['m'], j['p'], j['dist'])
                    fitness = self.eval_func(n=j['n'], p=j['p'], m=j['m'], dist=j['dist'], medians=result['medians'])
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Loads one or more cases from the input file for the p-median problem, optimized for speed.
        This version uses NumPy to perform the Floyd–Warshall algorithm in a vectorized manner,
        which is significantly faster than the pure-Python triple nested loops for moderate-to-large graphs.
        The input is expected to have one or more cases. Each case starts with a header line
        containing three numbers: n m p, where:
            - n: number of vertices,
            - m: number of edges,
            - p: number of medians to choose.
        This is followed by at least m non-empty lines, each specifying an edge in the format:
            i j cost
        (If there are more than m edge lines, only the first m valid ones are used.)
        For each case, the function builds the complete cost matrix by:
          - Initializing an n x n NumPy array with infinity (and 0 on the diagonal).
          - Processing m valid edges (using the last occurrence for duplicate edges).
          - Running a vectorized Floyd–Warshall algorithm to compute all-pairs shortest paths.
        Returns:
            A list of dictionaries, one per case. Each dictionary contains:
                - 'n': int, number of vertices.
                - 'm': int, number of edges.
                - 'p': int, number of medians to choose.
                - 'dist': list of lists, the complete cost matrix (n x n), converted from a NumPy array.
        """
        import numpy as np
        import math

        INF = math.inf

        # Read the entire file and filter out empty lines
        all_lines = [line.strip() for line in input_string.split('\n')]

        cases = []
        idx = 0
        while idx < len(all_lines):
            header_parts = all_lines[idx].split()
            idx += 1
            if len(header_parts) < 3:
                raise ValueError("Header line must contain at least three numbers: n, m, p.")
            try:
                n = int(header_parts[0])
                m = int(header_parts[1])
                p = int(header_parts[2])
            except Exception as e:
                raise ValueError("Invalid header values.") from e

            # Initialize the cost matrix using NumPy for fast operations.
            dist = np.full((n, n), INF, dtype=float)
            np.fill_diagonal(dist, 0.0)

            edges_read = 0
            while edges_read < m and idx < len(all_lines):
                tokens = all_lines[idx].split()
                idx += 1
                if len(tokens) < 3:
                    continue
                try:
                    u = int(tokens[0])
                    v = int(tokens[1])
                    c = float(tokens[2])
                except Exception:
                    continue
                if 1 <= u <= n and 1 <= v <= n:
                    # Update both symmetric entries; the last occurrence overwrites previous ones.
                    dist[u - 1, v - 1] = c
                    dist[v - 1, u - 1] = c
                edges_read += 1

            # Vectorized Floyd–Warshall: update distances using broadcasting.
            for k in range(n):
                # Update: dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j]) for all i, j.
                dist = np.minimum(dist, dist[:, k:k + 1] + dist[k:k + 1, :])

            # Convert the NumPy array to a list of lists for compatibility.
            cases.append({
                "n": n,
                "m": m,
                "p": p,
                "dist": dist.tolist()
            })

        return cases

    def eval_func(self, **kwargs):
        """
        Evaluates a candidate solution for the uncapacitated p-median problem.
        Parameters:
            candidate_data (dict): Contains the input data for a single case with keys:
                - 'n': int, number of vertices.
                - 'm': int, number of edges.
                - 'p': int, number of medians to choose.
                - 'dist': list of lists, the complete cost matrix (n x n).
            solution (dict): The candidate solution with key:
                - 'medians': list of exactly p distinct integers (each between 1 and n).
        Returns:
            float: The total assignment cost, i.e., the sum over all vertices of the shortest distance
                   to the nearest chosen median.
        Raises:
            ValueError: If the solution is invalid due to incorrect format, duplicates, out-of-range values,
                        or if any vertex is unreachable from all medians.
        """
        n = kwargs.get("n")
        p = kwargs.get("p")
        dist = kwargs.get("dist")
        medians = kwargs.get("medians", [])

        # Validate input constraints
        if not isinstance(n, int) or n <= 0:
            raise ValueError("Invalid number of vertices (n). Must be a positive integer.")
        if not isinstance(p, int) or p <= 0 or p > n:
            raise ValueError("Invalid number of medians (p). Must be a positive integer and at most n.")
        if not isinstance(dist, list) or len(dist) != n or any(len(row) != n for row in dist):
            raise ValueError("Invalid distance matrix. Must be a square matrix of size (n x n).")
        if not isinstance(medians, list) or len(medians) != p:
            raise ValueError(f"Medians must be a list of exactly {p} distinct integers.")
        if len(set(medians)) != p:
            raise ValueError("Medians must be distinct values.")
        if any(not isinstance(m, int) or m < 1 or m > n for m in medians):
            raise ValueError("Each median must be an integer in the range [1, n].")

        INF = float('inf')
        total_cost = 0.0

        for i in range(n):
            best_distance = INF
            for median in medians:
                d = dist[i][median - 1]  # Adjust for 0-indexing.
                if d < best_distance:
                    best_distance = d
            if best_distance == INF:
                raise ValueError(f"Vertex {i + 1} is unreachable from all chosen medians.")
            total_cost += best_distance

        return total_cost

    def norm_score(self, results):
        optimal_scores = {
            "pmed1.txt": [5819],
            "pmed2.txt": [4093],
            "pmed3.txt": [4250],
            "pmed4.txt": [3034],
            "pmed5.txt": [1355],
            "pmed6.txt": [7824],
            "pmed7.txt": [5631],
            "pmed8.txt": [4445],
            "pmed9.txt": [2734],
            "pmed10.txt": [1255],
            "pmed11.txt": [7696],
            "pmed12.txt": [6634],
            "pmed13.txt": [4374],
            "pmed14.txt": [2968],
            "pmed15.txt": [1729],
            "pmed16.txt": [8162],
            "pmed17.txt": [6999],
            "pmed18.txt": [4809],
            "pmed19.txt": [2845],
            "pmed20.txt": [1789],
            "pmed21.txt": [9138],
            "pmed22.txt": [8579],
            "pmed23.txt": [4619],
            "pmed24.txt": [2961],
            "pmed25.txt": [1828],
            "pmed26.txt": [9917],
            "pmed27.txt": [8307],
            "pmed28.txt": [4498],
            "pmed29.txt": [3033],
            "pmed30.txt": [1989],
            "pmed31.txt": [10086],
            "pmed32.txt": [9297],
            "pmed33.txt": [4700],
            "pmed34.txt": [3013],
            "pmed35.txt": [10400],
            "pmed36.txt": [9934],
            "pmed37.txt": [5057],
            "pmed38.txt": [11060],
            "pmed39.txt": [9423],
            "pmed40.txt": [5128]
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
        dev = {'pmed1.txt': [], 'pmed11.txt': [], 'pmed13.txt': [],
               'pmed15.txt': [], 'pmed17.txt': [], 'pmed19.txt': [],
               'pmed21.txt': [], 'pmed23.txt': [], 'pmed25.txt': [],
               'pmed27.txt': [], 'pmed29.txt': [], 'pmed3.txt': [],
               'pmed31.txt': [], 'pmed33.txt': [], 'pmed35.txt': [],
               'pmed37.txt': [], 'pmed39.txt': [], 'pmed5.txt': [],
               'pmed7.txt': [], 'pmed9.txt': []}

        return dev






