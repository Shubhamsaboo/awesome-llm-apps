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
from llm4ad.task.optimization.co_bench.multidimensional_knapsack_problem_co_bench.template import template_program, task_description

__all__ = ['MKPEvaluationCB']


class MKPEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Multidimensional knapsack problem")
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
                    result = eva(j['n'], j['m'], j['p'], j['r'], j['b'])
                    fitness = self.eval_func(j['n'], j['m'], j['p'], j['r'], j['b'], result['x'], j['opt'])
                    fitness_list.append(fitness)

            return np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data2(self, input_path):
        """
        Loads instance(s) from the OR-Library mknap2.txt file.
        This file contains many lines of commentary and then one or more instances.
        Each instance is defined (after removing comments) as:
          <#knapsacks> <#objects>
          <weights of objects>       (there will be exactly #objects numbers)
          <knapsack capacities>        (exactly #knapsacks numbers)
          <matrix of resource consumptions>   (#objects rows, each with #knapsacks numbers)
          [<known optimum>]           (an extra token, optional)
        In our formulation:
          - the number of decision variables (n) is set to the number of objects,
          - the number of constraints (m) is set to the number of knapsacks,
          - the profit coefficients p are taken equal to the object weights,
          - the constraint coefficients r are taken from the matrix (transposed so that each
            constraint i gets a list of consumptions for all objects),
          - the right-hand sides b are the knapsack capacities.
        Returns:
          A list of dictionaries. Each dictionary corresponds to one problem instance and
          has the keys:
             'n' : int, number of objects (decision variables)
             'm' : int, number of knapsacks (constraints)
             'p' : list of floats, profit coefficients (length n)
             'r' : list of m lists of floats, where each inner list is of length n (constraint coefficients)
             'b' : list of floats, knapsack capacities (length m)
          If the instance file also provides an optimum value, it is stored under key 'opt'.
        """
        cases = []
        all_lines = [line.strip() for line in input_string.split('\n')]

        # Remove comments (anything after '//') and extra whitespace.
        cleaned_lines = []
        for line in all_lines:
            line = line.split("//")[0]
            line = line.strip()
            if line:
                cleaned_lines.append(line)

        # Gather all tokens (they may come from several lines)
        tokens = []
        for line in cleaned_lines:
            tokens.extend(line.split())

        # Process tokens sequentially looking for candidate instance headers.
        # The expected header is two positive numbers: (#knapsacks, #objects).
        i = 0
        N = len(tokens)
        while i < N - 1:
            try:
                # Try to read two numbers as candidate header
                knapsacks = int(float(tokens[i]))
                objects = int(float(tokens[i + 1]))
            except Exception:
                i += 1
                continue

            # Basic validity check: both numbers must be positive.
            if knapsacks <= 0 or objects <= 0:
                i += 1
                continue

            # Once a candidate header is found, compute the expected number of tokens:
            # header already consumed: 2 tokens
            # then: object weights: objects tokens
            # then: knapsack capacities: knapsacks tokens
            # then: resource consumption matrix: objects * knapsacks tokens
            # Optionally: one token for known optimum.
            required = objects + knapsacks + (objects * knapsacks)
            # Check if there is at least the required number of tokens after the header.
            if i + 2 + required > N:
                # Not enough tokens left; break out.
                break

            # Consume header.
            i += 2

            # Read object weights (which we use as profit coefficients).
            weights = []
            for _ in range(objects):
                weights.append(float(tokens[i]))
                i += 1

            # Read knapsack capacities.
            capacities = []
            for _ in range(knapsacks):
                capacities.append(float(tokens[i]))
                i += 1

            # Read the resource consumption matrix.
            # The file gives a matrix with 'objects' rows and 'knapsacks' columns.
            matrix = []
            for _ in range(objects):
                row = []
                for _ in range(knapsacks):
                    row.append(float(tokens[i]))
                    i += 1
                matrix.append(row)

            # Optionally, read the known optimum if present.
            optimum = None
            if i < N:
                # We treat the next token as optimum if it is a number.
                try:
                    optimum = float(tokens[i])
                    i += 1
                except Exception:
                    optimum = None

            # Convert the data to our formulation:
            # Decision variables: one per object.
            # Constraints: one per knapsack.
            # Profit coefficients p: equal to the object weights.
            # Constraint coefficients r: we need to transpose the matrix so that for each knapsack,
            # we get the consumption for each object.
            p = weights
            r = []
            for k in range(knapsacks):
                constraint_coeffs = []
                for obj in range(objects):
                    constraint_coeffs.append(matrix[obj][k])
                r.append(constraint_coeffs)
            b = capacities

            case = {'n': objects, 'm': knapsacks, 'p': p, 'r': r, 'b': b}
            if optimum is not None:
                case['opt'] = optimum
            cases.append(case)

        return cases

    def load_data(self, input_string):
        """
        Reads the input string and returns a list of test cases.
        Each case is represented as a dictionary containing:
            - 'n': number of decision variables.
            - 'm': number of constraints.
            - 'p': list of floats, profit coefficients.
            - 'r': list of m lists of floats, constraint coefficients.
            - 'b': list of floats, right-hand side values.
        """
        # Simple check for mknap2 format - for now, use default format
        # if 'mknap2' in input_path:
        #     return self.load_data2(input_path)

        tokens = input_string.split()

        token_index = 0
        try:
            K = int(tokens[token_index])
        except Exception as e:
            raise ValueError("The first token must be an integer indicating the number of test cases.") from e
        token_index += 1

        cases = []
        for case_index in range(K):
            try:
                n = int(tokens[token_index])
                m = int(tokens[token_index + 1])
                opt_val = float(tokens[token_index + 2])
            except Exception as e:
                raise ValueError(f"Error reading header for test case {case_index + 1}.") from e
            token_index += 3

            p = []
            for j in range(n):
                try:
                    p.append(float(tokens[token_index]))
                except Exception as e:
                    raise ValueError(f"Error reading profit coefficient {j + 1} for test case {case_index + 1}.") from e
                token_index += 1

            r = []
            for i in range(m):
                row = []
                for j in range(n):
                    try:
                        row.append(float(tokens[token_index]))
                    except Exception as e:
                        raise ValueError(
                            f"Error reading constraint coefficient for constraint {i + 1}, variable {j + 1} in test case {case_index + 1}.") from e
                    token_index += 1
                r.append(row)

            b = []
            for i in range(m):
                try:
                    b.append(float(tokens[token_index]))
                except Exception as e:
                    raise ValueError(
                        f"Error reading right-hand side value {i + 1} for test case {case_index + 1}.") from e
                token_index += 1

            case_data = {
                'n': n,
                'm': m,
                'p': p,
                'r': r,
                'b': b,
                'opt': opt_val
            }
            cases.append(case_data)

        return cases

    def eval_func(self, n, m, p, r, b, x, opt=None):
        """
        Evaluates the solution for a multidimensional knapsack problem instance.
        Inputs:
          - n: int, number of decision variables.
          - m: int, number of constraints.
          - p: list of floats, profit coefficients (length n).
          - r: list of m lists of floats, each representing the constraint coefficients.
          - b: list of floats, right-hand side values for each constraint (length m).
          - x: list of ints (0 or 1), the solution decisions (length n).
          - opt (float, optional): The known optimal (or best-known) objective value.
            This parameter is provided by instances loaded via load_data2, if available.
        Evaluation:
          - The objective value is computed as:
                sum(p[j] * x[j] for j in range(n))
          - For each constraint i, the total resource consumption is computed as:
                sum(r[i][j] * x[j] for j in range(n))
          - If any constraint i is violated (i.e., the consumption exceeds b[i]), an error is raised.
          - If all constraints are satisfied, the score is equal to the objective value.
        Returns:
          - If opt is not provided (None), returns a float representing the overall quality score.
          - If opt is provided, returns a tuple:
                (score, gap)
            where gap is defined as (score - opt), which indicates how far (or above)
            the computed score is relative to the known optimum.
        """
        tol = 1e-6

        # Compute objective value.
        objective_value = sum(p[j] * x[j] for j in range(n))

        # Check each constraint; raise an error if any constraint is violated.
        for i in range(m):
            lhs = sum(r[i][j] * x[j] for j in range(n))
            if lhs - b[i] > tol:
                raise ValueError(f"Constraint violation in constraint {i}: consumption {lhs} exceeds limit {b[i]}.")

        # If all constraints are satisfied, score is the objective value.
        score = objective_value

        # Return either score alone or (score, gap) if optimum is provided.
        if opt is not None:
            gap = score - opt
            return score
        else:
            return score

    def norm_score(self, results):
        optimal_scores = {
            "mknap1.txt": [3800, 8706.1, 4015, 6120, 12400, 10618, 16537],
            "mknap2.txt": [7772.0, 8722.0, 141278.0, 130883.0, 95677.0, 119337.0, 98796.0, 130623.0, 1095445.0,
                           624319.0,
                           4554.0, 4536.0, 4115.0, 4561.0, 4514.0, 5557.0, 5567.0, 5605.0, 5246.0, 6339.0, 5643.0,
                           6339.0,
                           6159.0, 6954.0, 7486.0, 7289.0, 8633.0, 9580.0, 7698.0, 9450.0, 9074.0, 8947.0, 8344.0,
                           10220.0,
                           9939.0, 9584.0, 9819.0, 9492.0, 9410.0, 11191.0, 3090.0, 3186.0, 95168.0, 2139.0, 776.0,
                           1035.0,
                           3418.0, 3186.0],
            "mknapcb1.txt": [24381, 24274, 23551, 23534, 23991, 24613, 25591, 23410, 24216, 24411, 42757, 42545, 41968,
                             45090, 42218, 42927, 42009, 45020, 43441, 44554, 59822, 62081, 59802, 60479, 61091, 58959,
                             61538, 61520, 59453, 59965],
            "mknapcb2.txt": [59312, 61472, 62130, 59446, 58951, 60056, 60414, 61472, 61885, 58959, 109109, 109841,
                             108489,
                             109383, 110720, 110256, 109016, 109037, 109957, 107038, 149659, 155940, 149316, 152130,
                             150353,
                             150045, 148607, 149772, 155075, 154662],
            "mknapcb3.txt": [120130, 117837, 121109, 120798, 122319, 122007, 119113, 120568, 121575, 120699, 218422,
                             221191,
                             217534, 223558, 218962, 220514, 219987, 218194, 216976, 219693, 295828, 308077, 299796,
                             306476,
                             300342, 302560, 301322, 306430, 302814, 299904],
            "mknapcb4.txt": [23064, 22801, 22131, 22772, 22751, 22777, 21875, 22635, 22511, 22702, 41395, 42344, 42401,
                             45624, 41884, 42995, 43559, 42970, 42212, 41207, 57375, 58978, 58391, 61966, 60803, 61437,
                             56377, 59391, 60205, 60633],
            "mknapcb5.txt": [59187, 58662, 58094, 61000, 58092, 58803, 58607, 58917, 59384, 59193, 110863, 108659,
                             108932,
                             110037, 108423, 110841, 106075, 106686, 109825, 106723, 151790, 148772, 151900, 151275,
                             151948,
                             152109, 153131, 153520, 149155, 149704],
            "mknapcb6.txt": [117726, 119139, 119159, 118802, 116434, 119454, 119749, 118288, 117779, 119125, 217318,
                             219022,
                             217772, 216802, 213809, 215013, 217896, 219949, 214332, 220833, 304344, 302332, 302354,
                             300743,
                             304344, 301730, 304949, 296437, 301313, 307014],
            "mknapcb7.txt": [21946, 21716, 20754, 21464, 21814, 22176, 21799, 21397, 22493, 20983, 40767, 41304, 41560,
                             41041, 40872, 41058, 41062, 42719, 42230, 41700, 57494, 60027, 58025, 60776, 58884, 60011,
                             58132, 59064, 58975, 60603],
            "mknapcb8.txt": [56693, 58318, 56553, 56863, 56629, 57119, 56292, 56403, 57442, 56447, 107689, 108338,
                             106385,
                             106796, 107396, 107246, 106308, 103993, 106835, 105751, 150083, 149907, 152993, 153169,
                             150287,
                             148544, 147471, 152841, 149568, 149572],
            'mknapcb9.txt': [115868, 114667, 116661, 115237, 116353, 115604, 113952, 114199, 115247, 116947, 217995,
                             214534,
                             215854, 217836, 215566, 215762, 215772, 216336, 217290, 214624, 301627, 299985, 304995,
                             301935,
                             304404, 296894, 303233, 306944, 303057, 300460]
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
                    normed_scores.append(score / optimal_list[idx])
                else:
                    normed_scores.append(score)
            normed[case] = (normed_scores, error_message)

        return normed

    def get_dev(self):
        dev = {'mknap1.txt': [4, 1, 0],
               'mknap2.txt': [6, 44, 18, 22, 35, 45, 26, 28, 12, 0, 46, 1, 17, 31, 9, 21, 20, 23, 2, 13, 27, 33, 29,
                              41],
               'mknapcb1.txt': [2, 5, 24, 4, 6, 25, 8, 14, 11, 9, 20, 26, 10, 7, 27],
               'mknapcb2.txt': [18, 10, 4, 27, 16, 17, 25, 29, 13, 21, 20, 7, 14, 9, 28],
               'mknapcb3.txt': [2, 8, 3, 0, 18, 7, 24, 1, 17, 23, 28, 12, 9, 4, 5],
               'mknapcb4.txt': [9, 16, 2, 10, 24, 19, 3, 13, 14, 29, 28, 15, 0, 4, 22],
               'mknapcb5.txt': [16, 15, 11, 5, 7, 8, 20, 2, 3, 27, 12, 22, 29, 23, 21],
               'mknapcb6.txt': [23, 5, 9, 14, 13, 6, 7, 16, 8, 2, 22, 3, 25, 26, 1],
               'mknapcb7.txt': [22, 7, 11, 0, 4, 3, 26, 17, 10, 14, 8, 13, 27, 15, 9],
               'mknapcb8.txt': [19, 12, 18, 6, 0, 16, 2, 25, 15, 28, 14, 1, 26, 9, 4],
               'mknapcb9.txt': [23, 8, 21, 24, 0, 5, 17, 1, 2, 7, 27, 29, 15, 12, 18]}

        return dev





