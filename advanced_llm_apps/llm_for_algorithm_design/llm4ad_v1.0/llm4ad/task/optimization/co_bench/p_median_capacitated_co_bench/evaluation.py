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
from llm4ad.task.optimization.co_bench.p_median_capacitated_co_bench.template import template_program, task_description

__all__ = ['PMCEvaluationCB']


class PMCEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "p-median - capacitated")
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
                    result = eva(j['best_known'], j['n'], j['p'], j['Q'], j['customers'])
                    fitness = self.eval_func(best_known=j['best_known'], n=j['n'], p=j['p'], Q=j['Q'], objective=result['objective'], medians=result['medians'], assignments=result['assignments'])
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Load one or more instances of the Capacitated P-Median Problem from a text file.
        The input file structure is:
          Line 1: An integer M, the number of problem instances in the file.
          Then, for each instance:
              - A header line with two values: <problem_number> <best_known_solution_value>
              - A line with three values: <n> <p> <Q>
              - n subsequent lines each with: <customer_number> <x_coordinate> <y_coordinate> <demand>
        Returns:
          A list of dictionaries. Each dictionary contains the keys:
             - 'best_known': float
             - 'n': int
             - 'p': int
             - 'Q': float
             - 'customers': list of tuples (customer_id, x, y, demand)
        """
        cases = []
        try:
            lines = [line.strip() for line in input_string.split('\n') if line.strip() != '']
        except Exception as e:
            raise ValueError("Error reading input file: " + str(e))

        if not lines:
            raise ValueError("Input file is empty.")

        try:
            M = int(lines[0])
        except Exception as e:
            raise ValueError("The first line must be an integer representing the number of cases.")

        index = 1
        for case_idx in range(M):
            if index >= len(lines):
                raise ValueError("Unexpected end of file when reading case {}.".format(case_idx + 1))

            # Read problem header: <problem_number> <best_known_solution_value>
            tokens = lines[index].split()
            if len(tokens) < 2:
                raise ValueError("Invalid problem header at case {}.".format(case_idx + 1))
            try:
                # We don't need the problem number, so we can ignore it.
                _ = int(tokens[0])
                best_known = float(tokens[1])
            except Exception as e:
                raise ValueError("Error parsing problem header at case {}: {}".format(case_idx + 1, e))
            index += 1

            if index >= len(lines):
                raise ValueError("Missing instance parameters for case {}.".format(case_idx + 1))

            # Read instance parameters: <n> <p> <Q>
            tokens = lines[index].split()
            if len(tokens) < 3:
                raise ValueError("Invalid instance parameters at case {}.".format(case_idx + 1))
            try:
                n = int(tokens[0])
                p = int(tokens[1])
                Q = float(tokens[2])
            except Exception as e:
                raise ValueError("Error parsing instance parameters at case {}: {}".format(case_idx + 1, e))
            index += 1

            # Read n customer lines
            customers = []
            if len(lines) < index + n:
                raise ValueError("Expected {} customer lines for case {}, but found fewer.".format(n, case_idx + 1))
            for i in range(n):
                tokens = lines[index].split()
                if len(tokens) < 4:
                    raise ValueError("Invalid customer data at line {} in case {}.".format(index + 1, case_idx + 1))
                try:
                    customer_id = int(tokens[0])
                    x = float(tokens[1])
                    y = float(tokens[2])
                    demand = float(tokens[3])
                except Exception as e:
                    raise ValueError(
                        "Error parsing customer data on line {} in case {}: {}".format(index + 1, case_idx + 1, e))
                customers.append((customer_id, x, y, demand))
                index += 1

            case_data = {
                "best_known": best_known,
                "n": n,
                "p": p,
                "Q": Q,
                "customers": customers
            }
            cases.append(case_data)

        return cases

    def eval_func(self, **kwargs):
        """
        Evaluate the solution for a single instance of the Capacitated P-Median Problem.
        This function expects the following keyword arguments (combined from the instance data and the solution):
          - best_known (float): Best known solution value (for reference).
          - n (int): Number of customers.
          - p (int): Number of medians.
          - Q (float): Capacity of each median.
          - customers (list of tuples): Each tuple is (customer_id, x, y, demand).
          - objective (numeric): The objective value (total cost) reported by the solution.
          - medians (list of int): List of chosen medians (customer IDs), exactly p elements.
          - assignments (list of int): List of assignments for each customer (length n), where each entry is one of the chosen medians.
        The evaluation performs the following:
          1. Verifies that each assignment is to one of the selected medians.
          2. Checks that the total demand assigned to each median does not exceed Q.
          3. Recomputes the total cost as the sum, over all customers, of the Euclidean distance (rounded down)
             from the customer to its assigned median.
          4. Computes the score as: score = best_known / computed_total_cost.
        Returns:
          A scalar float representing the score for the solution.
        """
        import math

        # Extract instance data
        best_known = kwargs.get("best_known")
        n = kwargs.get("n")
        p = kwargs.get("p")
        Q = kwargs.get("Q")
        customers = kwargs.get("customers")

        # Extract solution data
        reported_obj = kwargs.get("objective")
        medians = kwargs.get("medians")
        assignments = kwargs.get("assignments")

        if best_known is None or n is None or p is None or Q is None or customers is None:
            raise ValueError("Instance data is incomplete.")
        if reported_obj is None or medians is None or assignments is None:
            raise ValueError("Solution data is incomplete.")

        # Validate medians length
        if len(medians) != p:
            raise ValueError("The solution must contain exactly {} medians; found {}.".format(p, len(medians)))

        # Validate assignments length
        if len(assignments) != n:
            raise ValueError("The solution must contain exactly {} assignments; found {}.".format(n, len(assignments)))

        # Build a dictionary for quick lookup of customer data by customer_id.
        cust_dict = {}
        for cust in customers:
            cid, x, y, demand = cust
            cust_dict[cid] = (x, y, demand)

        # Verify that each median is a valid customer.
        for m in medians:
            if m not in cust_dict:
                raise ValueError("Median {} is not found in the customer data.".format(m))

        # Verify that each customer's assignment is one of the selected medians.
        for idx, a in enumerate(assignments):
            if a not in medians:
                raise ValueError(
                    "Customer {} is assigned to {} which is not in the list of selected medians.".format(idx + 1, a))

        # Check capacity constraints.
        capacity_usage = {m: 0.0 for m in medians}
        for i, a in enumerate(assignments):
            # Assuming that the order of customers in 'customers' corresponds to customer 1..n.
            demand = customers[i][3]
            capacity_usage[a] += demand
        for m, used in capacity_usage.items():
            if used > Q + 1e-6:  # small tolerance
                raise ValueError(
                    "Capacity exceeded for median {}: used capacity {:.4f} exceeds allowed capacity {:.4f}.".format(m,
                                                                                                                    used,
                                                                                                                    Q))

        # Recompute the total cost.
        total_cost = 0
        for i, a in enumerate(assignments):
            # Get customer i data.
            try:
                cid, cx, cy, _ = customers[i]
            except Exception as e:
                raise ValueError("Error accessing data for customer {}: {}".format(i + 1, e))
            # Get the assigned median's coordinates.
            if a not in cust_dict:
                raise ValueError("Assigned median {} for customer {} not found.".format(a, i + 1))
            mx, my, _ = cust_dict[a]
            d = math.sqrt((cx - mx) ** 2 + (cy - my) ** 2)
            total_cost += math.floor(d)

        if total_cost <= 0:
            raise ValueError("Computed total cost is non-positive, which is invalid.")

        score = best_known / total_cost
        return score

    def get_dev(self):
        dev = {'pmedcap1.txt': [3, 11, 16, 0, 4, 2, 1, 9, 19, 18]}

        return dev





