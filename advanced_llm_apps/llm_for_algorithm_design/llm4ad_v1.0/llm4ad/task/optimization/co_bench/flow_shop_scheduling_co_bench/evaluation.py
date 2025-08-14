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
from llm4ad.task.optimization.co_bench.flow_shop_scheduling_co_bench.template import template_program, task_description

__all__ = ['FSSEvaluationCB']


class FSSEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Flow shop scheduling")
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
                    result = eva(j['n'], j['m'], j['matrix'])
                    fitness = self.eval_func(n=j['n'], m=j['m'], matrix=j['matrix'], job_sequence=result['job_sequence'], lower_bound=j['lower_bound'], upper_bound=j['upper_bound'])
                    fitness_list.append(fitness)

            return np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Reads a file containing multiple test cases for the flow shop scheduling problem.
        The file format:
          - A header line: "number of jobs, number of machines, initial seed, upper bound and lower bound :"
          - Next line: five numbers (n, m, seed, upper_bound, lower_bound)
          - A line that starts with "processing times :"
          - Then m lines of processing times. Each line contains n integers (processing times for one machine across all jobs).
        The function returns a list of test cases, where each test case is a dictionary with:
          - "n" (int): number of jobs
          - "m" (int): number of machines
          - "matrix" (list of list of int): processing times in a n x m matrix (each row corresponds to a job)
          - "upper_bound" (int)
          - "lower_bound" (int)
        """
        test_cases = []
        all_lines = [line.strip() for line in input_string.split('\n')]

        i = 0
        while i < len(all_lines):
            line = all_lines[i].strip()
            # Look for the header line indicating a new test case.
            if line.startswith("number of jobs"):
                # Skip to the line with the five numbers.
                i += 1
                while i < len(all_lines) and all_lines[i].strip() == "":
                    i += 1
                if i >= len(all_lines):
                    break
                # The header values line (n, m, seed, upper_bound, lower_bound)
                header_tokens = all_lines[i].strip().split()
                if len(header_tokens) < 5:
                    raise ValueError(f"Expected at least 5 numbers in header, got: {all_lines[i].strip()}")
                n = int(header_tokens[0])
                m = int(header_tokens[1])
                # initial seed is ignored
                upper_bound = int(header_tokens[3])
                lower_bound = int(header_tokens[4])
                i += 1

                # Skip empty lines until we find the processing times label.
                while i < len(all_lines) and all_lines[i].strip() == "":
                    i += 1
                # Expect a line that starts with "processing times"
                if i < len(all_lines) and all_lines[i].strip().lower().startswith("processing times"):
                    i += 1
                else:
                    raise ValueError("Expected 'processing times' line not found.")

                # Read m lines containing the processing times (each line should have n integers)
                machine_times = []
                for _ in range(m):
                    while i < len(all_lines) and all_lines[i].strip() == "":
                        i += 1
                    if i >= len(all_lines):
                        raise ValueError("Unexpected end of file while reading processing times.")
                    row_tokens = all_lines[i].strip().split()
                    if len(row_tokens) != n:
                        raise ValueError(
                            f"Expected {n} numbers in processing times line, got {len(row_tokens)} in line: {all_lines[i].strip()}")
                    row = [int(token) for token in row_tokens]
                    machine_times.append(row)
                    i += 1

                # The data is read per machine, so transpose it to obtain a list of n jobs,
                # where each job is a list of m processing times.
                matrix = [[machine_times[machine][job] for machine in range(m)] for job in range(n)]

                # Add the test case dictionary.
                test_cases.append({
                    "n": n,
                    "m": m,
                    "matrix": matrix,
                    "upper_bound": upper_bound,
                    "lower_bound": lower_bound
                })
            else:
                i += 1

        return test_cases

    # def load_flowshop1(self, input_path):
    #     """
    #     Reads the input file for one or more flow shop scheduling instances.
    #     The file may contain multiple cases. For each case, the instance is defined by:
    #       - A header section (to be skipped) until a line with exactly two integers is found.
    #       - The two integers define n (number of jobs) and m (number of machines).
    #       - Then the next n nonempty lines (ignoring blank lines and lines starting with '+')
    #         contain the job descriptions. Each job line must contain at least 2*m integers,
    #         which are interpreted as (machine, processing_time) pairs.
    #       - The processing times for each job are collected and ordered by machine number (0 to m-1).
    #     Returns:
    #       list: A list of dictionaries, each corresponding to one instance/case with keys:
    #             - 'n': number of jobs (int)
    #             - 'm': number of machines (int)
    #             - 'matrix': list of list of int (each sublist contains processing times for one job)
    #     """
    #     if 'tai' in input_path:
    #         return load_tai(input_path)
    #
    #     cases = []
    #     try:
    #         with open(input_path, 'r') as f:
    #             lines = f.readlines()
    #     except Exception as e:
    #         raise Exception("Error reading input file: " + str(e))
    #
    #     line_index = 0
    #     total_lines = len(lines)
    #
    #     while line_index < total_lines:
    #         # Search for a valid instance size line (exactly two integers)
    #         instance_found = False
    #         while line_index < total_lines:
    #             line = lines[line_index].strip()
    #             line_index += 1
    #             if not line:
    #                 continue
    #             tokens = line.split()
    #             if len(tokens) == 2:
    #                 try:
    #                     n_val = int(tokens[0])
    #                     m_val = int(tokens[1])
    #                     n, m = n_val, m_val
    #                     instance_found = True
    #                     break
    #                 except ValueError:
    #                     continue
    #         if not instance_found:
    #             break  # No more instances found
    #
    #         matrix = []
    #         job_count = 0
    #         # Read next n valid job lines (skip blank and lines starting with '+')
    #         while line_index < total_lines and job_count < n:
    #             line = lines[line_index].strip()
    #             line_index += 1
    #             if not line or line.startswith('+'):
    #                 continue
    #             tokens = line.split()
    #             if len(tokens) < 2 * m:
    #                 raise Exception(
    #                     f"Error: Expected at least {2 * m} numbers in a job line, got {len(tokens)} in line: {line}")
    #             # Consider only the first 2*m tokens in case of extra tokens.
    #             tokens = tokens[:2 * m]
    #             try:
    #                 numbers = [int(token) for token in tokens]
    #             except ValueError:
    #                 raise Exception("Error: Non-integer token encountered in job line.")
    #
    #             job_data = {}
    #             for i in range(0, len(numbers), 2):
    #                 machine = numbers[i]
    #                 proc_time = numbers[i + 1]
    #                 if machine < 0 or machine >= m:
    #                     raise Exception(f"Error: Invalid machine number {machine} (expected between 0 and {m - 1}).")
    #                 if machine in job_data:
    #                     raise Exception(f"Error: Duplicate machine number {machine} in job line.")
    #                 job_data[machine] = proc_time
    #             if set(job_data.keys()) != set(range(m)):
    #                 raise Exception("Error: Not all machine numbers are present in job line.")
    #             job_proc = [job_data[i] for i in range(m)]
    #             matrix.append(job_proc)
    #             job_count += 1
    #
    #         if job_count != n:
    #             raise Exception("Error: Number of job lines read does not match the expected number of jobs.")
    #
    #         cases.append({'n': n, 'm': m, 'matrix': matrix})
    #
    #     return cases

    def eval_func(self, **kwargs):
        """
        Evaluates a flow shop scheduling solution for a single instance.
        Input kwargs must include:
          - n (int): Number of jobs.
          - m (int): Number of machines.
          - matrix (list of list of int): Processing times matrix.
          - job_sequence (list of int): A 1-indexed permutation of job indices, as returned by solve.
        The evaluation metric (makespan) is computed using the classical flow shop recurrence:
          - C[0][0] = processing_time(job_1, machine_0)
          - For the first job on machines j > 0: C[0][j] = C[0][j-1] + processing_time(job_1, machine_j)
          - For subsequent jobs on the first machine: C[i][0] = C[i-1][0] + processing_time(job_(i+1), machine_0)
          - For all other entries: C[i][j] = max(C[i-1][j], C[i][j-1]) + processing_time(job_(i+1), machine_j)
        Returns:
          float: The computed makespan for the provided solution.
        """
        n = kwargs.get('n')
        m = kwargs.get('m')
        matrix = kwargs.get('matrix')
        job_sequence = kwargs.get('job_sequence')

        # Validate the job sequence: it must be a permutation of [1, 2, ..., n]
        if not job_sequence or len(job_sequence) != n or set(job_sequence) != set(range(1, n + 1)):
            raise Exception(f"Error: Job sequence is not a valid permutation of job indices 1 to {n}.")

        # Convert job sequence from 1-indexed to 0-indexed.
        seq_zero = [job - 1 for job in job_sequence]

        # Initialize the completion time table.
        completion = [[0] * m for _ in range(n)]

        for i in range(n):
            for j in range(m):
                proc_time = matrix[seq_zero[i]][j]
                if i == 0 and j == 0:
                    completion[i][j] = proc_time
                elif i == 0:
                    completion[i][j] = completion[i][j - 1] + proc_time
                elif j == 0:
                    completion[i][j] = completion[i - 1][j] + proc_time
                else:
                    completion[i][j] = max(completion[i - 1][j], completion[i][j - 1]) + proc_time

        makespan = completion[-1][-1]

        score = kwargs['lower_bound'] / makespan
        # score = kwargs['upper_bound'] / makespan
        return score

    def get_dev(self):
        dev = {'tai100_10.txt': [1, 7, 4, 9, 8], 'tai100_20.txt': [1, 0, 2, 6, 8], 'tai100_5.txt': [9, 8, 5, 6, 3],
               'tai200_10.txt': [5, 9, 4, 1, 0], 'tai200_20.txt': [9, 4, 7, 6, 0], 'tai20_10.txt': [8, 9, 2, 5, 4],
               'tai20_20.txt': [4, 8, 9, 7, 6], 'tai20_5.txt': [7, 3, 9, 8, 0], 'tai500_20.txt': [3, 0, 6, 7, 4],
               'tai50_10.txt': [6, 4, 3, 8, 7], 'tai50_20.txt': [1, 7, 4, 6, 2], 'tai50_5.txt': [6, 7, 2, 4, 8]}

        return dev




