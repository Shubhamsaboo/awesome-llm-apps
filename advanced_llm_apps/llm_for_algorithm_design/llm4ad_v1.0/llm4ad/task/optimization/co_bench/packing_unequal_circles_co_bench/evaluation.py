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
from llm4ad.task.optimization.co_bench.packing_unequal_circles_co_bench.template import template_program, task_description

__all__ = ['PUCEvaluationCB']


class PUCEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Packing unequal circles")
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
                    result = eva(j['n'], j['cx'], j['cy'], j['R'], j['radii'])
                    fitness = self.eval_func(n=j['n'], cx=j['cx'], cy=j['cy'], R=j['R'], radii=j['radii'], coords=result['coords'])
                    fitness_list.append(fitness)

            return np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Load and parse the input file containing one or multiple cases.
        File Format:
          - The file is a plain-text file with non-empty lines.
          - Each case starts with a header line containing exactly four numbers:
                n cx cy R
            where:
              • n  is the number of circles (an integer),
              • cx and cy are the container's center coordinates (floats),
              • R  is the container's radius (float).
          - The next n non-empty lines each contain one real number representing
            the radius of a circle.
        Returns:
          A list of cases, where each case is a dictionary with keys:
              "n"     : int, number of circles.
              "cx"    : float, container center x-coordinate.
              "cy"    : float, container center y-coordinate.
              "R"     : float, container radius.
              "radii" : list of float, the radii of the circles.
        """
        cases = []
        try:
            lines = [line.strip() for line in input_string.split('\n') if line.strip() != '']
        except Exception as e:
            raise Exception(f"Error reading input file: {e}")

        i = 0
        total_lines = len(lines)
        while i < total_lines:
            header_tokens = lines[i].split()
            if len(header_tokens) != 4:
                raise Exception(f"Header line at line {i + 1} must contain exactly 4 numbers: n cx cy R.")
            try:
                n = int(header_tokens[0])
                cx = float(header_tokens[1])
                cy = float(header_tokens[2])
                R = float(header_tokens[3])
            except Exception as e:
                raise Exception(f"Error parsing header on line {i + 1}: {e}")

            if i + n >= total_lines:
                raise Exception(f"Not enough lines for {n} circle radii after line {i + 1}.")
            radii = []
            for j in range(1, n + 1):
                try:
                    # Even if there are extra tokens, take the first as the radius.
                    r = float(lines[i + j].split()[0])
                    radii.append(r)
                except Exception as e:
                    raise Exception(f"Error parsing circle radius on line {i + j + 1}: {e}")
            case = {"n": n, "cx": cx, "cy": cy, "R": R, "radii": radii}
            cases.append(case)
            i += n + 1  # Move to the next case header (if any)
        return cases

    def eval_func(self, **kwargs):
        """
        Evaluate the solution for the Maximise Number problem of Unequal Circle Packing.
        Input (merged from the case data and the solution):
          - n     : int, the total number of circles.
          - cx    : float, x-coordinate of the container's center.
          - cy    : float, y-coordinate of the container's center.
          - R     : float, the container's radius.
          - radii : list of float, radii for each circle (assumed sorted in increasing order).
          - coords: list of (x, y) tuples, the centers of the circles as produced by solve.
        Evaluation Details:
          1. Identify “packed” circles. By convention, a circle is considered packed if its coordinate
             is not equal to the default (cx, cy) (within tolerance). For the maximize number problem,
             the optimal solution packs a prefix of the sorted circles.
          2. Verify the prefix property: if any circle i is packed, then all circles with index < i must also be packed.
          3. For every packed circle:
             - Check container feasibility:
                 Ensure that sqrt((x-cx)^2 + (y-cy)^2) + r_i <= R.
             - Record the clearance: R - (distance to (cx,cy) + r_i).
          4. For every pair of packed circles, verify non-overlap:
                 Ensure that distance((x_i,y_i), (x_j,y_j)) >= r_i + r_j.
             And record the pair clearance.
          5. If any feasibility constraint is violated (beyond a small tolerance), raise an error.
          6. Let the primary score be the number of circles packed (i.e. the prefix length).
             Use the minimum clearance among packed circles as a tie-breaker.
             (For example, final score = (number packed) + ε*(minimum clearance), with ε small.)
        Returns:
          float: the evaluation score (a higher score indicates a better solution).
                 The main component is the number of circles feasibly packed.
        """
        import math

        tol = 1e-5  # Numerical tolerance.

        # Extract required inputs.
        try:
            n = kwargs["n"]
            cx = kwargs["cx"]
            cy = kwargs["cy"]
            container_R = kwargs["R"]
            radii = kwargs["radii"]
            coords = kwargs["coords"]
        except KeyError as e:
            raise Exception(f"Missing required parameter: {e}")

        if len(coords) != n:
            raise Exception(f"Expected {n} coordinates, but got {len(coords)}.")

        # Identify packed circles.
        # Convention: a circle is considered not packed if its center is (cx, cy) within tolerance.
        packed_indices = []
        for i in range(n):
            x, y = coords[i]
            if x != -1 and y != -1:
                # if math.sqrt((x - cx) ** 2 + (y - cy) ** 2) > tol:
                packed_indices.append(i)

        # Verify the prefix property: if a circle with index i is packed, then all circles with index < i must be packed.
        if packed_indices:
            K = max(packed_indices)  # highest index among packed circles.
            for i in range(K):
                if i not in packed_indices:
                    raise Exception(f"Prefix property violated: circle {i} is not packed while circle {K} is packed.")
        else:
            K = -1  # No circles packed.

        # Evaluate feasibility of packed circles.
        container_clearances = []
        for i in packed_indices:
            x, y = coords[i]
            r = radii[i]
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            clearance = container_R - (dist + r)
            if clearance < -tol:
                raise Exception(f"Circle {i} violates container constraint by {-clearance}.")
            container_clearances.append(clearance)

        pair_clearances = []
        for idx, i in enumerate(packed_indices):
            for j in packed_indices[idx + 1:]:
                x1, y1 = coords[i]
                x2, y2 = coords[j]
                center_distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                required_distance = radii[i] + radii[j]
                clearance = center_distance - required_distance
                if clearance < -tol:
                    raise Exception(f"Circles {i} and {j} overlap by {-clearance}.")
                pair_clearances.append(clearance)

        # Primary measure: number of circles packed.
        # (Since indices are 0-based, number_packed = K+1 if any are packed.)
        num_packed = (K + 1) if packed_indices else 0

        # Final score: primary is the count of packed circles; use clearance as a tie-breaker.
        score = num_packed
        return score

    def norm_score(self, results):
        optimal_scores = {
            "circle1.txt": [6],
            "circle2.txt": [15],
            "circle3.txt": [22],
            "circle4.txt": [30],
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






