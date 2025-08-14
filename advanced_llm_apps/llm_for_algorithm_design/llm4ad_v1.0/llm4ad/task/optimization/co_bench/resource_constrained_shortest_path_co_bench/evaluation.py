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
from llm4ad.task.optimization.co_bench.resource_constrained_shortest_path_co_bench.template import template_program, task_description

__all__ = ['RCSPEvaluationCB']


class RCSPEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Resource constrained shortest path")
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
                    result = eva(j['n'], j['m'], j['K'], j['R'], j['lower_bounds'], j['upper_bounds'], j['vertex_resources'], j['graph'])
                    fitness = self.eval_func(j['n'], j['m'], j['K'], j['R'], j['lower_bounds'], j['upper_bounds'], j['vertex_resources'], j['graph'], result['total_cost'], result['path'])
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Load one or more cases from a TXT input file for the Resource Constrained Shortest Path problem.
        The input file format (per case) is as follows:
          1. Three numbers: n (number of vertices), m (number of arcs), K (number of resources)
          2. For each resource (k = 1,...,K): the lower limit on the resource consumed on the chosen path.
          3. For each resource (k = 1,...,K): the upper limit on the resource consumed on the chosen path.
          4. For each vertex (i = 1,...,n): K numbers indicating the resource consumption incurred at that vertex.
          5. For each arc (j = 1,...,m): (3 + K) numbers:
                 - starting vertex,
                 - ending vertex,
                 - cost of the arc,
                 - K numbers indicating the resource consumption incurred on the arc.
        Note:
          In many of the RCSP test files, the file is a stream of numbers separated by whitespace rather than fixed lines.
          This implementation reads the entire file and splits it into tokens.
        Returns:
          A list of cases. Each case is a dictionary with keys:
             "n", "m", "K", "lower_bounds", "upper_bounds", "vertex_resources", "graph"
        """
        tokens = input_string.split()

        cases = []
        pos = 0
        total_tokens = len(tokens)

        while pos < total_tokens:
            if pos + 3 > total_tokens:
                break  # Not enough tokens for a new case header.
            try:
                n = int(tokens[pos])
                m = int(tokens[pos + 1])
                K = int(tokens[pos + 2])
            except Exception as e:
                raise ValueError("Error reading header (n, m, K)") from e
            pos += 3

            if pos + K > total_tokens:
                raise ValueError("Not enough tokens for lower bounds.")
            lower_bounds = [float(tokens[pos + i]) for i in range(K)]
            pos += K

            if pos + K > total_tokens:
                raise ValueError("Not enough tokens for upper bounds.")
            upper_bounds = [float(tokens[pos + i]) for i in range(K)]
            pos += K

            if pos + n * K > total_tokens:
                raise ValueError("Not enough tokens for vertex resource consumption.")
            vertex_resources = []
            for i in range(n):
                vertex_resources.append([float(tokens[pos + j]) for j in range(K)])
                pos += K

            if pos + m * (3 + K) > total_tokens:
                raise ValueError("Not enough tokens for arc information.")
            graph = {i: [] for i in range(1, n + 1)}
            for j in range(m):
                try:
                    u = int(tokens[pos])
                    v = int(tokens[pos + 1])
                    cost = float(tokens[pos + 2])
                    arc_resources = [float(tokens[pos + 3 + i]) for i in range(K)]
                except Exception as e:
                    raise ValueError("Error reading arc information.") from e
                pos += 3 + K
                graph[u].append((v, cost, arc_resources))

            case = {
                "n": n,
                "m": m,
                "K": K,
                "lower_bounds": lower_bounds,
                "upper_bounds": upper_bounds,
                "vertex_resources": vertex_resources,
                "graph": graph
            }
            cases.append(case)

        return cases

    def eval_func(self, n, m, K, lower_bounds, upper_bounds, vertex_resources, graph, total_cost, path):
        """
        Evaluate the solution for one case of the Resource Constrained Shortest Path problem.
        Parameters:
          n, m, K                : Input parameters defining the problem instance.
          lower_bounds           : List of lower resource bounds (length K).
          upper_bounds           : List of upper resource bounds (length K).
          vertex_resources       : List (length n) of lists (each of length K) with resource consumption per vertex.
          graph                  : Dictionary mapping each vertex (1-indexed) to its outgoing arcs.
                                   Each arc is a tuple (end_vertex, cost, [arc resource consumptions]).
          total_cost             : The total cost value reported by the solution (not used in validation).
          path                   : List of vertex indices (integers) defining the computed path.
        Returns:
          The total arc cost along the path if the solution is valid.
        Raises:
          ValueError: If the solution is invalid (i.e. the path does not start at vertex 1, does not end at vertex n,
                      contains an undefined arc, or the cumulative resource consumption (from both vertices and arcs)
                      is not within the specified bounds for each resource).
        """

        # Check basic validity of the path.
        if not path or path[0] != 1 or path[-1] != n:
            raise ValueError("Invalid solution: path must start at vertex 1 and end at vertex n.")

        computed_cost = 0.0
        total_resources = [0.0] * K

        # Add resource consumption from vertices.
        for vertex in path:
            if vertex < 1 or vertex > n:
                raise ValueError(f"Invalid solution: vertex {vertex} is out of valid range 1 to {n}.")
            for k in range(K):
                total_resources[k] += vertex_resources[vertex - 1][k]

        # For each consecutive pair in the path, check for a valid arc and add its cost and resource consumption.
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i + 1]
            valid_arc = False
            for (dest, arc_cost, arc_res) in graph.get(u, []):
                if dest == v:
                    valid_arc = True
                    computed_cost += arc_cost
                    for k in range(K):
                        total_resources[k] += arc_res[k]
                    break
            if not valid_arc:
                raise ValueError(f"Invalid solution: no valid arc from vertex {u} to vertex {v}.")

        # Verify resource constraints.
        for k in range(K):
            if total_resources[k] < lower_bounds[k] - 1e-6 or total_resources[k] > upper_bounds[k] + 1e-6:
                raise ValueError(
                    f"Invalid solution: total consumption for resource {k} is {total_resources[k]}, "
                    f"which is outside the bounds [{lower_bounds[k]}, {upper_bounds[k]}]."
                )

        return computed_cost

    def norm_score(self, results):
        optimal_scores = {
            "rcsp1.txt": [88.3],
            "rcsp2.txt": [131],
            "rcsp3.txt": [1.44],
            "rcsp4.txt": [2],
            "rcsp5.txt": [81.9],
            "rcsp6.txt": [91.4],
            "rcsp7.txt": [3.91],
            "rcsp8.txt": [3.77],
            "rcsp9.txt": [420],
            "rcsp10.txt": [420],
            "rcsp11.txt": [6],
            "rcsp12.txt": [6],
            "rcsp13.txt": [448],
            "rcsp14.txt": [656],
            "rcsp15.txt": [6.2],
            "rcsp16.txt": [5],
            "rcsp17.txt": [487],
            "rcsp18.txt": [512],
            "rcsp19.txt": [6],
            "rcsp20.txt": [6],
            "rcsp21.txt": [858],
            "rcsp22.txt": [858],
            "rcsp23.txt": [3.34],
            "rcsp24.txt": [3.74]
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
        dev = {'rcsp1.txt': [], 'rcsp11.txt': [], 'rcsp13.txt': [],
               'rcsp15.txt': [], 'rcsp17.txt': [], 'rcsp19.txt': [],
               'rcsp21.txt': [], 'rcsp23.txt': [], 'rcsp3.txt': [],
               'rcsp5.txt': [], 'rcsp7.txt': [], 'rcsp9.txt': []}

        return dev






