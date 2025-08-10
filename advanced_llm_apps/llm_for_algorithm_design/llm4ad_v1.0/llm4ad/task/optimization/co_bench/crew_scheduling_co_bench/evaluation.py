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
from llm4ad.task.optimization.co_bench.crew_scheduling_co_bench.template import template_program, task_description

__all__ = ['CSchedulingEvaluationCB']


class CSchedulingEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Crew scheduling")
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
                    result = eva(j['N'], j['K'], j['time_limit'], j['tasks'], j['arcs'])
                    fitness = self.eval_func(N=j['N'], K=j['K'], time_limit=j['time_limit'], tasks=j['tasks'], arcs=j['arcs'], crews=result['crews'])
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Loads input data from a provided text string. This function supports multiple cases.
        The input file format for each case is as follows:
          - The first line contains two numbers: the number of tasks (N) and the maximum allowed duty time (time_limit).
          - The next N lines contain two numbers each: start time and finish time for each task (tasks are indexed from 1 to N).
          - The remaining lines describe transition arcs between tasks in the format: "i j cost".
        Cases are assumed to be separated by one or more blank lines.
        Returns:
          list: A list of dictionaries, each dictionary corresponds to one case with keys:
                "N", "time_limit", "tasks", "arcs".
        """
        cases = []
        try:
            lines = [line.strip() for line in input_string.split('\n') if line.strip() != '']
        except Exception as e:
            raise ValueError("Failed to read input string: " + str(e))

        # Split lines into blocks separated by blank lines.
        blocks = []
        current_block = []
        for line in lines:
            if line.strip() == "":
                if current_block:
                    blocks.append(current_block)
                    current_block = []
            else:
                current_block.append(line.strip())
        if current_block:
            blocks.append(current_block)

        # Parse each block as a separate case.
        for block in blocks:
            if not block:
                continue
            # Parse the first line: number of tasks and time limit.
            first_parts = block[0].split()
            if len(first_parts) < 2:
                raise ValueError("The first line must contain at least two values: number of tasks and time limit.")
            try:
                N = int(first_parts[0])
                time_limit = float(first_parts[1])
            except Exception as e:
                raise ValueError("Error parsing number of tasks or time limit: " + str(e))

            if len(block) < 1 + N:
                raise ValueError(f"Expected {N} task lines after the first line; found {len(block) - 1}.")

            tasks = {}
            # Parse tasks: next N lines.
            for i in range(1, 1 + N):
                parts = block[i].split()
                if len(parts) < 2:
                    raise ValueError(f"Task line {i} does not contain two values.")
                try:
                    start_time = float(parts[0])
                    finish_time = float(parts[1])
                except Exception as e:
                    raise ValueError(f"Invalid time values in task line {i}: " + str(e))
                tasks[i] = (start_time, finish_time)

            # Parse remaining lines: transition arcs.
            arcs = {}
            for line in block[1 + N:]:
                parts = line.split()
                if len(parts) < 3:
                    continue  # Ignore lines that don't have the complete triple.
                try:
                    from_task = int(parts[0])
                    to_task = int(parts[1])
                    cost = float(parts[2])
                except Exception:
                    continue  # Skip lines with invalid formatting.
                arcs[(from_task, to_task)] = cost

            case_data = {"N": N, "time_limit": time_limit, "tasks": tasks, "arcs": arcs}

            # Determine K range based on problem size (N)
            if N <= 50:
                k_range = range(27, 32)
            elif N <= 100:
                k_range = range(44, 49)
            elif N <= 150:
                k_range = range(69, 74)
            elif N <= 200:
                k_range = range(93, 98)
            elif N <= 250:
                k_range = range(108, 113)
            elif N <= 300:
                k_range = range(130, 134)
            elif N <= 350:
                k_range = range(144, 149)
            elif N <= 400:
                k_range = range(159, 164)
            elif N <= 450:
                k_range = range(182, 187)
            else:  # N <= 500 or larger
                k_range = range(204, 209)
            
            for k in k_range:
                cases.append(case_data | {'K': k})

        return cases

    def eval_func(self, **kwargs):
        """
        Evaluates the quality (i.e. total cost and feasibility) of a crew scheduling solution.
        Raises an error immediately if any feasibility constraint is violated.
        Input kwargs must include:
          - N (int): Number of tasks.
          - K (int): The exact number of crews required.
          - time_limit (float): Maximum allowed duty time.
          - tasks (dict): Mapping from task ID to (start_time, finish_time).
          - arcs (dict): Mapping from (from_task, to_task) to transition cost.
          - crews (list): List of lists, where each inner list is the sequence of task IDs for one crew.
        Returns:
          float: The total transition cost if the solution is feasible.
        """
        N = kwargs.get("N")
        K = kwargs.get("K")
        time_limit = kwargs.get("time_limit")
        tasks = kwargs.get("tasks")
        arcs = kwargs.get("arcs")
        crews = kwargs.get("crews")

        if crews is None:
            raise ValueError("Solution does not contain a 'crews' key.")

        # Check that exactly K crews are used.
        if K is None:
            raise ValueError("Parameter K (number of crews) is missing.")
        if len(crews) > K:
            raise ValueError(f"Invalid solution: number of crews in solution is larger than K={K}.")

        # Validate that every task appears exactly once.
        all_tasks_in_output = [task for crew in crews for task in crew]
        if len(all_tasks_in_output) != N:
            raise ValueError("Invalid solution: number of tasks in crews does not equal N.")
        if set(all_tasks_in_output) != set(range(1, N + 1)):
            raise ValueError("Invalid solution: tasks in crews do not match expected tasks set.")

        total_cost = 0.0

        # Evaluate each crew schedule.
        for crew in crews:
            if not crew:
                raise ValueError("Invalid solution: one crew has an empty schedule.")

            # Check the duty time.
            first_task = crew[0]
            last_task = crew[-1]
            duty_time = tasks[last_task][1] - tasks[first_task][0]
            if duty_time > time_limit:
                raise ValueError("Invalid solution: duty time for a crew exceeds the time limit.")

            # Check each consecutive pair of tasks.
            for idx in range(len(crew) - 1):
                current_task = crew[idx]
                next_task = crew[idx + 1]

                # Check that tasks do not overlap.
                if tasks[current_task][1] > tasks[next_task][0]:
                    raise ValueError(f"Invalid solution: tasks {current_task} and {next_task} overlap.")

                # Check that a valid transition arc exists.
                if (current_task, next_task) not in arcs:
                    raise ValueError(
                        f"Invalid solution: missing transition arc between tasks {current_task} and {next_task}.")

                # Add the transition cost.
                total_cost += arcs[(current_task, next_task)]

        return total_cost

    def norm_score(self, results):
        optimal_scores = {
            'csp50.txt': [3139, 2706, 2399, 2092, 1872],
            'csp100.txt': [4812, 4514, 4310, 4107, 3905],
            'csp150.txt': [6275, 5999, 5754, 5551, 5347],
            'csp200.txt': [6914, 6747, 6583, 6430, 6288],
            'csp250.txt': [8406, 8212, 8023, 7863, 7707],
            'csp300.txt': [9580, 9378, 9200, 9026],
            'csp350.txt': [10991, 10833, 10677, 10525, 10378],
            'csp400.txt': [12341, 12163, 12006, 11848, 11696],
            'csp450.txt': [12785, 12639, 12497, 12357, 12232],
            'csp500.txt': [13302, 13169, 13032, 12899, 12772],
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
        dev = {'csp100.txt': [2, 1], 'csp150.txt': [1, 4], 'csp200.txt': [4, 2], 'csp250.txt': [2, 1],
               'csp300.txt': [2, 0],
               'csp350.txt': [4, 3], 'csp400.txt': [2, 0], 'csp450.txt': [2, 1], 'csp50.txt': [1, 0],
               'csp500.txt': [4, 1]}

        return dev


