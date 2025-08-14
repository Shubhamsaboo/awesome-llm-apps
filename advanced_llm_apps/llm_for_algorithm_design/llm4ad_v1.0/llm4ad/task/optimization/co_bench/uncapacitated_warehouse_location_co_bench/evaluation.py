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
from llm4ad.task.optimization.co_bench.uncapacitated_warehouse_location_co_bench.template import template_program, task_description

__all__ = ['UWLEvaluationCB']


class UWLEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Uncapacitated warehouse location")
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
                    result = eva(j['m'], j['n'], j['warehouses'], j['customers'])
                    fitness = self.eval_func(j['m'], j['n'], j['warehouses'], j['customers'], result['warehouse_open'], result['assignments'])
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Reads one or more problem cases from the input file.
        Expected Input File Format for each case:
          Line 1: Two integers: m n
          Next m lines: Each line contains two numbers: capacity fixed_cost for a warehouse.
          Next n lines: Each line contains: demand (a number) followed by m numbers representing the cost of
                      allocating the customer's demand to each warehouse.
        If the input file contains multiple cases, the cases appear sequentially in the file.
        Returns:
          A list of dictionaries, each corresponding to one case. Each dictionary has the keys:
             - 'm': Number of potential warehouses (int)
             - 'n': Number of customers (int)
             - 'warehouses': List of dictionaries; each with keys 'capacity' and 'fixed_cost'
             - 'customers': List of dictionaries; each with keys 'demand' and 'costs' (list of floats)
        """
        try:
            all_lines = [line.strip() for line in input_string.split('\n')]
        except Exception as e:
            raise ValueError("Error reading input file: " + str(e))

        # Tokenize all non-empty lines.
        tokens = []
        for line in all_lines:
            line = line.strip()
            if line:
                tokens.extend(line.split())

        cases = []
        index = 0
        total_tokens = len(tokens)

        # Process tokens until we have exhausted them.
        while index < total_tokens:
            if index + 1 >= total_tokens:
                raise ValueError("Insufficient tokens to read m and n for a case.")
            try:
                m = int(tokens[index])
                n = int(tokens[index + 1])
            except Exception as e:
                raise ValueError("Error parsing m or n: " + str(e))
            index += 2

            # Parse warehouse data (m warehouses, each with 2 tokens).
            expected_warehouse_tokens = m * 2
            if index + expected_warehouse_tokens - 1 >= total_tokens:
                raise ValueError("Not enough tokens for warehouse data in a case.")
            warehouses = []
            for i in range(m):
                try:
                    capacity = float(tokens[index])
                    fixed_cost = float(tokens[index + 1])
                except Exception as e:
                    raise ValueError("Error parsing warehouse data: " + str(e))
                warehouses.append({'capacity': capacity, 'fixed_cost': fixed_cost})
                index += 2

            # Parse customer data (n customers, each with 1 demand and m cost values).
            customers = []
            for j in range(n):
                if index >= total_tokens:
                    raise ValueError(f"Not enough tokens for customer {j + 1} demand.")
                try:
                    demand = float(tokens[index])
                except Exception as e:
                    raise ValueError(f"Error parsing demand for customer {j + 1}: " + str(e))
                index += 1
                if index + m - 1 >= total_tokens:
                    raise ValueError(f"Not enough tokens for cost data for customer {j + 1}.")
                costs = []
                for i in range(m):
                    try:
                        cost = float(tokens[index])
                    except Exception as e:
                        raise ValueError(f"Error parsing cost for customer {j + 1}, warehouse {i + 1}: " + str(e))
                    costs.append(cost)
                    index += 1
                customers.append({'demand': demand, 'costs': costs})

            case_data = {"m": m, "n": n, "warehouses": warehouses, "customers": customers}
            cases.append(case_data)

        return cases

    def eval_func(self, m, n, warehouses, customers, warehouse_open, assignments, **kwargs):
        """
        Evaluates the solution for the Uncapacitated Warehouse Location Problem.
        For each customer:
          - The customer must be assigned to exactly one open warehouse.
          - The assignment cost is the cost associated with the warehouse to which the customer is assigned.
          - No assignment is allowed for a warehouse that is closed.
        The total cost is computed as:
             (Sum of fixed costs for all open warehouses)
           + (Sum of assignment costs for all customers)
        Input Parameters:
          - m: Number of potential warehouses (int)
          - n: Number of customers (int)
          - warehouses: List of dictionaries, each with keys:
                'fixed_cost': The fixed cost for opening the warehouse.
                'capacity': Provided but ignored in this problem.
          - customers: List of dictionaries, each with keys:
                'costs': A list of floats representing the cost of assigning the customer entirely to each warehouse.
                'demand': Provided but ignored in this problem.
          - warehouse_open: List of m integers (0 or 1) indicating whether each warehouse is closed or open.
          - assignments: List of n lists (each of length m) where assignments[j][i] is 1 if customer j is assigned to warehouse i, and 0 otherwise.
          - kwargs: Other parameters (not used here).
        Returns:
          A floating-point number representing the total cost if the solution is feasible.
        Raises:
          Exception: If any of the following conditions are violated:
              - The sum of assignments for any customer is not exactly 1.
              - Any positive assignment is made to a closed warehouse.
              - Any assignment value is not binary (0 or 1).
        """
        computed_total_cost = 0.0

        # Add fixed costs for open warehouses.
        for i in range(m):
            if warehouse_open[i] == 1:
                computed_total_cost += warehouses[i]['fixed_cost']

        # Evaluate assignment cost for each customer.
        for j in range(n):
            # Sum of assignments for customer j should be exactly 1.
            assigned_sum = sum(assignments[j])
            if abs(assigned_sum - 1.0) > 1e-6:
                raise Exception(
                    f"Customer {j} assignment violation: total assigned value {assigned_sum} does not equal 1."
                )

            customer_cost = 0.0
            for i in range(m):
                allocation = assignments[j][i]
                # Ensure the assignment is binary (allowing for small floating point tolerance)
                if not (abs(allocation) < 1e-6 or abs(allocation - 1.0) < 1e-6):
                    raise Exception(
                        f"Customer {j} has a non-binary assignment value {allocation} for warehouse {i + 1}."
                    )
                if allocation > 0:
                    if warehouse_open[i] != 1:
                        raise Exception(
                            f"Customer {j} is assigned to warehouse {i + 1}, which is closed."
                        )
                    # Since assignment is binary, add the corresponding cost.
                    customer_cost += customers[j]['costs'][i]
            computed_total_cost += customer_cost

        return computed_total_cost

    def norm_score(self, results):
        optimal_scores = {
            "cap71.txt": [932615.750],
            "cap72.txt": [977799.400],
            "cap73.txt": [1010641.450],
            "cap74.txt": [1034976.975],
            "cap101.txt": [796648.437],
            "cap102.txt": [854704.200],
            "cap103.txt": [893782.112],
            "cap104.txt": [928941.750],
            "cap131.txt": [793439.562],
            "cap132.txt": [851495.325],
            "cap133.txt": [893076.712],
            "cap134.txt": [928941.750],
            "capa.txt": [17156454.478],
            "capb.txt": [12979071.582],
            "capc.txt": [11505594.329]
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
        dev = {'cap101.txt': [], 'cap103.txt': [],
               'cap131.txt': [],
               'cap133.txt': [],
               'cap71.txt': [], 'cap73.txt': [],
               'capb.txt': []}

        return dev

