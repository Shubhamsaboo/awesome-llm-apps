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
from llm4ad.task.optimization.co_bench.generalised_assignment_problem_co_bench.template import template_program, task_description

__all__ = ['GAPEvaluationCB']


class GAPEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Generalised assignment problem")
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
                    result = eva(j['m'], j['n'], j['cost_matrix'], j['consumption_matrix'], j['capacities'], j['problem_type'])
                    fitness = self.eval_func(j['m'], j['n'], j['cost_matrix'], j['consumption_matrix'], j['capacities'], result['assignments'])
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Load and parse the input file for the Generalised Assignment Problem (GAP).
        The input is expected to be a whitespace‐delimited text file with the following format:
          - The first token is an integer P, indicating the number of cases.
          - For each case, the following tokens are provided sequentially:
              • Two integers: m (number of agents) and n (number of jobs).
              • m×n numbers representing the cost matrix (row by row).
              • m×n numbers representing the resource consumption matrix (row by row).
              • m numbers representing the capacities for each agent.
        Parameters:
          input_file_path: (str) Path to the input text file.
        Returns:
          A list of dictionaries. Each dictionary corresponds to one case and contains the keys:
              'm', 'n', 'cost_matrix', 'consumption_matrix', and 'capacities'.
        """
        cases = []
        try:
            tokens = input_string.split()
        except Exception as e:
            raise Exception("Error reading input file: " + str(e))

        ptr = 0
        try:
            P = int(tokens[ptr])
            ptr += 1
        except Exception as e:
            raise Exception("Error parsing the number of cases: " + str(e))

        for _ in range(P):
            try:
                m = int(tokens[ptr])
                n = int(tokens[ptr + 1])
                ptr += 2
            except Exception as e:
                raise Exception("Error parsing m and n for a case: " + str(e))

            cost_matrix = []
            for i in range(m):
                row = []
                for j in range(n):
                    try:
                        row.append(float(tokens[ptr]))
                    except Exception as e:
                        raise Exception("Error reading cost matrix value: " + str(e))
                    ptr += 1
                cost_matrix.append(row)

            consumption_matrix = []
            for i in range(m):
                row = []
                for j in range(n):
                    try:
                        row.append(float(tokens[ptr]))
                    except Exception as e:
                        raise Exception("Error reading consumption matrix value: " + str(e))
                    ptr += 1
                consumption_matrix.append(row)

            capacities = []
            for i in range(m):
                try:
                    capacities.append(float(tokens[ptr]))
                except Exception as e:
                    raise Exception("Error reading capacity value: " + str(e))
                ptr += 1
            # Determine problem type based on content analysis or default to 'max'
            # Since we don't have file name, we'll default to 'max' for now
            problem_type = 'max'

            case = {
                'm': m,
                'n': n,
                'cost_matrix': cost_matrix,
                'consumption_matrix': consumption_matrix,
                'capacities': capacities,
                'problem_type': problem_type
            }
            cases.append(case)

        return cases

    def eval_func(self, m, n, cost_matrix, consumption_matrix, capacities, assignments, **kwargs):
        """
        Evaluate a solution for a single case of the Generalised Assignment Problem (GAP).
        Parameters:
          - m: (int) Number of agents.
          - n: (int) Number of jobs.
          - cost_matrix: (list of list of float) The cost matrix of size m×n.
          - consumption_matrix: (list of list of float) The resource consumption matrix of size m×n.
          - capacities: (list of float) The resource capacities for each of the m agents.
          - assignments: (list of int) A list of n integers (using 1-indexing) representing the agent
                         assigned to each job.
        Evaluation:
          - TotalCost is computed as the sum of cost_matrix[agent-1][j] for each job j.
          - For each agent i, ResourceConsumption[i] is the sum of consumption_matrix[i][j] for jobs assigned to agent i.
          - If an agent’s ResourceConsumption exceeds its capacity, a ValueError is raised.
          - For a maximization problem, the score is simply the TotalCost.
            (For minimization problems, you might use the negative of TotalCost.)
        Returns:
          A numeric score (float) evaluating the quality of the solution.
        """
        total_cost = 0.0
        agent_consumption = [0.0] * m

        # Check if the number of assignments matches the number of jobs.
        if len(assignments) != n:
            raise ValueError("Malformed solution: number of assignments does not match the number of jobs.")

        # Process each job.
        for j in range(n):
            agent = assignments[j]
            # Check if the assigned agent is valid (using 1-indexing).
            if agent < 1 or agent > m:
                raise ValueError(f"Invalid agent number {agent} for job {j}. Must be between 1 and {m}.")
            agent_index = agent - 1
            total_cost += cost_matrix[agent_index][j]
            agent_consumption[agent_index] += consumption_matrix[agent_index][j]

        # Check capacity constraints for each agent.
        for i in range(m):
            if agent_consumption[i] > capacities[i]:
                raise ValueError(
                    f"Capacity constraint violated for agent {i + 1}: consumption {agent_consumption[i]} exceeds capacity {capacities[i]}.")

        # For a feasible solution, return the total cost as the score (for a maximization problem).
        return total_cost

    def norm_score(self, results):
        # Pre-defined optimal scores for each test case.
        optimal_scores = {
            "gap1.txt": [336.0, 327.0, 339.0, 341.0, 326.0],
            "gap10.txt": [958.0, 963.0, 960.0, 947.0, 947.0],
            "gap11.txt": [1139.0, 1178.0, 1195.0, 1171.0, 1171.0],
            "gap12.txt": [1451.0, 1449.0, 1433.0, 1447.0, 1446.0],
            "gap2.txt": [434.0, 436.0, 420.0, 419.0, 428.0],
            "gap3.txt": [580.0, 564.0, 573.0, 570.0, 564.0],
            "gap4.txt": [656.0, 644.0, 673.0, 647.0, 664.0],
            "gap5.txt": [563.0, 558.0, 564.0, 568.0, 559.0],
            "gap6.txt": [761.0, 759.0, 758.0, 752.0, 747.0],
            "gap7.txt": [942.0, 949.0, 968.0, 945.0, 951.0],
            "gap8.txt": [1133.0, 1134.0, 1141.0, 1117.0, 1127.0],
            "gap9.txt": [709.0, 717.0, 712.0, 723.0, 706.0],
            "gapa.txt": [1698, 3235, 1360, 2623, 1158, 2339],
            "gapb.txt": [1843, 3553, 1407, 2831, 1166, 2340],
            "gapc.txt": [1931, 3458, 1403, 2814, 1244, 2397],
            "gapd.txt": [6373, 12796, 6379, 12601, 6269, 12452],
        }

        normed = {}
        for case, (scores, error_message) in results.items():
            if case not in optimal_scores:
                continue  # Skip if there's no optimal score defined.
            optimal_list = optimal_scores[case]
            normed_scores = []
            # Compute normalized score for each index.
            if 'gapa.txt' in case or 'gapb.txt' in case or 'gapc.txt' in case or 'gapd.txt' in case:
                problem_type = 'min'
            else:
                problem_type = 'max'
            for idx, score in enumerate(scores):
                if isinstance(score, (int, float)):
                    if problem_type == 'min':
                        normed_scores.append(optimal_list[idx] / score)
                    else:
                        normed_scores.append(score / optimal_list[idx])
                else:
                    normed_scores.append(score)
            normed[case] = (normed_scores, error_message)

        return normed

    def get_dev(self):
        dev = {'gap1.txt': [2, 3], 'gap10.txt': [2, 0], 'gap11.txt': [3, 0], 'gap12.txt': [3, 1], 'gap2.txt': [2, 1],
               'gap3.txt': [2, 1], 'gap4.txt': [2, 0], 'gap5.txt': [1, 4], 'gap6.txt': [2, 0], 'gap7.txt': [4, 1],
               'gap8.txt': [1, 4], 'gap9.txt': [1, 4], 'gapa.txt': [4, 0, 2], 'gapb.txt': [3, 2, 0],
               'gapc.txt': [3, 2, 0],
               'gapd.txt': [5, 4, 1]}

        return dev




