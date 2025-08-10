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
from llm4ad.task.optimization.co_bench.container_loading_co_bench.template import template_program, task_description

__all__ = ['CLEvaluationCB']


class CLEvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Container loading")
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
                    result = eva(j['problem_index'], j['container'], j['box_types'])
                    fitness = self.eval_func(j['problem_index'], j['container'], j['box_types'], result['placements'])
                    fitness_list.append(fitness)

            return np.mean(fitness_list)  # itself is a maximize problem

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Loads container loading problem data from string content.
        The input format:
          1. The first line is an integer P, the number of test problems.
          2. For each test problem:
             a. A header line with two integers: problem_index and a seed (the seed may be ignored).
                (Note: Some files may only provide one number; the seed is optional.)
             b. A line with three integers: container_length, container_width, container_height.
             c. A line with a single integer n: the number of box types.
             d. Then n lines follow, each with 7 or 8 integers in this order:
                    box_type, d1, f1, d2, f2, d3, f3 [, count]
                If only 7 numbers are provided, a default count of 1 is assumed.
        Returns:
          A list of dictionaries, one per test case. Each dictionary has the following keys:
             - 'problem_index': int,
             - 'container': tuple (container_length, container_width, container_height),
             - 'box_types': dict mapping each box_type to a dict with keys:
                   'dims': [d1, d2, d3],
                   'flags': [f1, f2, f3],
                   'count': count
        """
        test_cases = []
        lines = [line.strip() for line in input_string.split('\n') if line.strip()]
        if not lines:
            raise ValueError("Empty input file")

        try:
            P = int(lines[0])
        except Exception as e:
            raise ValueError("First line must be an integer representing the number of test cases.") from e
        idx = 1
        for case_num in range(P):
            # Read header: expecting at least one number (problem_index); seed is optional.
            header_parts = lines[idx].split()
            if len(header_parts) < 1:
                raise ValueError(f"Test case {case_num + 1}: Header line missing problem index.")
            problem_index = int(header_parts[0])
            idx += 1

            # Container dimensions: length, width, height.
            cont_parts = lines[idx].split()
            if len(cont_parts) < 3:
                raise ValueError(f"Test case {problem_index}: Container dimensions missing or incomplete.")
            container = tuple(map(int, cont_parts[:3]))
            idx += 1

            # Number of box types.
            if idx >= len(lines):
                raise ValueError(f"Test case {problem_index}: Expected number of box types but reached end of file.")
            try:
                n = int(lines[idx])
            except Exception as e:
                raise ValueError(f"Test case {problem_index}: Box types count is not an integer.") from e
            idx += 1

            box_types = {}
            for bt_index in range(n):
                if idx >= len(lines):
                    raise ValueError(
                        f"Test case {problem_index}: Missing box type specification at index {bt_index + 1}.")
                parts = lines[idx].split()
                if len(parts) < 7:
                    raise ValueError(
                        f"Test case {problem_index}: Box type specification incomplete on line: '{lines[idx]}'")
                try:
                    bt = int(parts[0])
                    d1 = int(parts[1])
                    f1 = int(parts[2])
                    d2 = int(parts[3])
                    f2 = int(parts[4])
                    d3 = int(parts[5])
                    f3 = int(parts[6])
                    # If a count is provided, use it; otherwise default to 1.
                    count = int(parts[7]) if len(parts) >= 8 else 1
                except Exception as e:
                    raise ValueError(
                        f"Test case {problem_index}: Error parsing box type specification: '{lines[idx]}'") from e
                dims = [d1, d2, d3]
                flags = [f1, f2, f3]
                box_types[bt] = {'dims': dims, 'flags': flags, 'count': count}
                idx += 1

            test_cases.append({
                'problem_index': problem_index,
                'container': container,
                'box_types': box_types
            })
        return test_cases

    def eval_func(self, problem_index, container, box_types, placements, **kwargs):
        """
        Evaluates a container loading solution for a single test case.
        Parameters:
          - problem_index: the integer identifier of the test case.
          - container: a tuple (container_length, container_width, container_height).
          - box_types: a dictionary mapping box types to their specifications.
          - placements: a list of placement dictionaries; each must include:
                'box_type', 'container_id', 'x', 'y', 'z', 'v', 'hswap'
        Returns:
          A scalar float value representing the volume utilization ratio if the solution is valid.
          If any placement is invalid (e.g., incorrect orientation, out-of-bound placement,
          overlapping boxes, or exceeding available count), the function returns 0.0.
        Evaluation Details:
          - For each placement, verifies that the chosen vertical dimension (v) is allowed.
          - Computes the oriented dimensions:
                horizontal dimensions are the two not chosen as vertical (swapped if hswap == 1),
                vertical dimension is dims[v].
          - Checks that each box is entirely within the container.
          - Checks that boxes do not overlap (touching is allowed).
          - Verifies that the number of placed boxes for each type does not exceed the available count.
          - The score is computed as (total placed volume) / (container volume).
        """

        def boxes_overlap(pos1, dims1, pos2, dims2):
            x1, y1, z1 = pos1
            w1, d1, h1 = dims1
            x2, y2, z2 = pos2
            w2, d2, h2 = dims2
            if x1 + w1 <= x2 or x2 + w2 <= x1:
                return False
            if y1 + d1 <= y2 or y2 + d2 <= y1:
                return False
            if z1 + h1 <= z2 or z2 + h2 <= z1:
                return False
            return True

        cont_len, cont_wid, cont_ht = container
        container_volume = cont_len * cont_wid * cont_ht
        total_placed_volume = 0
        used_counts = {}
        placements_by_container = {}

        # Group placements by container_id
        for pmt in placements:
            cid = pmt['container_id']
            if cid not in placements_by_container:
                placements_by_container[cid] = []
            placements_by_container[cid].append(pmt)

        # Validate each placement
        for cid, plist in placements_by_container.items():
            for pmt in plist:
                bt = pmt['box_type']
                if bt not in box_types:
                    return 0.0  # Unknown box type
                info = box_types[bt]
                dims = info['dims']
                flags = info['flags']
                v = pmt['v']
                if v not in [0, 1, 2]:
                    return 0.0
                if flags[v] != 1:
                    return 0.0  # Vertical orientation not allowed

                # Determine horizontal dimensions indices
                horz_idx = [i for i in [0, 1, 2] if i != v]
                h1 = dims[horz_idx[0]]
                h2 = dims[horz_idx[1]]
                if pmt['hswap'] == 1:
                    h1, h2 = h2, h1
                vert = dims[v]

                # Check that placement coordinates are nonnegative and within container bounds
                if pmt['x'] < 0 or pmt['y'] < 0 or pmt['z'] < 0:
                    return 0.0
                if (pmt['x'] + h1 > cont_len or
                        pmt['y'] + h2 > cont_wid or
                        pmt['z'] + vert > cont_ht):
                    return 0.0

                # Save oriented dimensions and position for overlap checking
                pmt['oriented_dims'] = (h1, h2, vert)
                pmt['oriented_pos'] = (pmt['x'], pmt['y'], pmt['z'])
                total_placed_volume += h1 * h2 * vert
                used_counts[bt] = used_counts.get(bt, 0) + 1

            # Check for overlaps among placements in the same container
            for i in range(len(plist)):
                for j in range(i + 1, len(plist)):
                    if boxes_overlap(plist[i]['oriented_pos'], plist[i]['oriented_dims'],
                                     plist[j]['oriented_pos'], plist[j]['oriented_dims']):
                        return 0.0

        # Verify that box usage does not exceed available counts
        for bt, cnt in used_counts.items():
            if cnt > box_types[bt]['count']:
                return 0.0

        utilization = total_placed_volume / container_volume if container_volume > 0 else 0.0
        return utilization

    def get_dev(self):
        dev = {
            'thpack1.txt': [89, 15, 12, 53, 78, 32, 56, 30, 6, 28, 23, 62, 52, 37, 69, 33, 35, 24, 17, 4, 79, 72, 2, 92,
                            54,
                            90, 91, 1, 57, 59, 94, 65, 25, 14, 83, 47, 46, 95, 48, 42, 88, 68, 85, 55, 40, 64, 74, 70,
                            3,
                            7],
            'thpack2.txt': [6, 9, 72, 24, 69, 2, 81, 33, 53, 39, 64, 71, 15, 99, 61, 36, 52, 8, 19, 7, 4, 1, 86, 21, 31,
                            5,
                            20, 57, 0, 79, 55, 35, 23, 25, 89, 44, 91, 62, 82, 12, 68, 75, 73, 27, 80, 56, 30, 47, 70,
                            16],
            'thpack3.txt': [17, 36, 89, 50, 19, 11, 97, 9, 75, 62, 10, 46, 42, 23, 39, 18, 99, 1, 5, 20, 70, 60, 31, 3,
                            43,
                            33, 51, 92, 95, 40, 84, 63, 13, 78, 58, 25, 4, 38, 24, 15, 88, 82, 7, 28, 8, 77, 71, 80, 76,
                            53],
            'thpack4.txt': [7, 89, 96, 75, 2, 37, 6, 82, 18, 14, 90, 36, 32, 40, 10, 25, 56, 72, 87, 98, 45, 21, 23, 55,
                            4,
                            79, 15, 65, 63, 73, 5, 81, 76, 69, 20, 67, 85, 60, 50, 47, 84, 16, 35, 1, 22, 43, 91, 48,
                            88,
                            41],
            'thpack5.txt': [79, 36, 97, 5, 62, 10, 49, 2, 23, 52, 51, 29, 96, 20, 64, 41, 38, 35, 94, 95, 12, 73, 34,
                            11,
                            93, 69, 58, 61, 87, 80, 71, 4, 88, 57, 46, 59, 33, 50, 13, 44, 0, 85, 55, 21, 77, 82, 63,
                            67,
                            31, 26],
            'thpack6.txt': [21, 31, 83, 22, 10, 19, 5, 0, 43, 82, 66, 36, 49, 38, 33, 58, 70, 15, 97, 80, 9, 30, 42, 88,
                            69,
                            61, 40, 60, 14, 95, 91, 39, 98, 16, 73, 90, 51, 18, 71, 26, 47, 54, 57, 87, 17, 53, 89, 92,
                            65,
                            81],
            'thpack7.txt': [97, 37, 73, 88, 50, 79, 12, 60, 99, 34, 4, 19, 78, 9, 7, 93, 31, 74, 90, 38, 33, 21, 24, 22,
                            52,
                            0, 43, 67, 13, 3, 59, 42, 39, 47, 36, 40, 45, 10, 5, 56, 57, 18, 51, 61, 92, 20, 69, 81, 35,
                            98],
            'thpack8.txt': [11, 4, 12, 14, 10, 2, 7],
            'thpack9.txt': [14, 32, 25, 30, 40, 8, 37, 15, 31, 9, 17, 21, 22, 16, 24, 33, 35, 44, 42, 0, 1, 45, 11]}

        return dev

