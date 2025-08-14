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
from llm4ad.task.optimization.co_bench.container_loading_with_weight_restrictions_co_bench.template import template_program, task_description

__all__ = ['CLWREvaluationCB']
TOL = 1e-6


class CLWREvaluationCB(Evaluation):

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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Container loading with weight restrictions")
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
                    result = eva(j['container'], j['n'], j['cargo_vol'], j['box_types'])
                    fitness = self.eval_func(j['container'], j['n'], j['cargo_vol'], j['box_types'], result['instance'], result['util'], result['m'], result['placements'])
                    fitness_list.append(fitness)

            return np.mean(fitness_list)  # itself is a maximize problem

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Loads the input data file for the Container Loading problem.
        The input file may contain one or more test cases. For each test case:
          - The first non-empty line contains three floats: container length, width, height (in cm).
          - The next non-empty line contains an integer n (number of box types) and a float (total cargo volume in m³).
          - The following n non-empty lines each contain 11 whitespace-separated values:
                Box length, length_flag, Box width, width_flag, Box height, height_flag,
                count, weight, lb1, lb2, lb3.
        Returns:
           A list where each element is a dictionary containing the input data for one test case with keys:
             'container', 'n', 'cargo_vol', and 'box_types'.
        """
        all_lines = [line.strip() for line in input_string.split('\n')]

        cases = []
        i = 0
        while i < len(all_lines):
            # Read container dimensions.
            parts = all_lines[i].split()
            if len(parts) < 3:
                raise ValueError("Invalid container dimensions line.")
            container = (int(parts[0]), int(parts[1]), int(parts[2]))
            i += 1

            # Read header: number of box types and cargo volume.
            parts = all_lines[i].split()
            if len(parts) < 2:
                raise ValueError("Invalid test-case header line.")
            n = int(parts[0])
            cargo_vol = float(parts[1])
            i += 1

            # Read details for each box type.
            box_types = []
            for _ in range(n):
                parts = all_lines[i].split()
                if len(parts) != 11:
                    raise ValueError("Invalid box type line: " + all_lines[i])
                box_type = {
                    'length': int(parts[0]),
                    'length_flag': int(parts[1]),
                    'width': int(parts[2]),
                    'width_flag': int(parts[3]),
                    'height': int(parts[4]),
                    'height_flag': int(parts[5]),
                    'count': int(parts[6]),
                    'weight': float(parts[7]),
                    'lb1': float(parts[8]),
                    'lb2': float(parts[9]),
                    'lb3': float(parts[10])
                }
                box_types.append(box_type)
                i += 1

            cases.append({
                'container': container,
                'n': n,
                'cargo_vol': cargo_vol,
                'box_types': box_types
            })

        return cases

    # Helper functions used by eval_func

    def get_box_dimensions(self, box, orientation):
        """
        Given a box type (dictionary) and an orientation (1, 2, or 3),
        returns a tuple (dx, dy, dz, lb, volume) where:
          - (dx, dy) are the horizontal dimensions,
          - dz is the vertical dimension,
          - lb is the load-bearing ability for that orientation,
          - volume is the original box volume.
        Orientation conventions:
          1: Box length is vertical (dz = length; horizontal: width, height).
          2: Box width is vertical (dz = width; horizontal: length, height).
          3: Box height is vertical (dz = height; horizontal: length, width).
        """
        if orientation == 1:
            if box['length_flag'] != 1:
                raise ValueError("Orientation 1 not allowed for this box type.")
            dz = box['length']
            dx = box['width']
            dy = box['height']
            lb = box['lb1']
        elif orientation == 2:
            if box['width_flag'] != 1:
                raise ValueError("Orientation 2 not allowed for this box type.")
            dz = box['width']
            dx = box['length']
            dy = box['height']
            lb = box['lb2']
        elif orientation == 3:
            if box['height_flag'] != 1:
                raise ValueError("Orientation 3 not allowed for this box type.")
            dz = box['height']
            dx = box['length']
            dy = box['width']
            lb = box['lb3']
        else:
            raise ValueError("Invalid orientation value.")
        volume = box['length'] * box['width'] * box['height']
        return dx, dy, dz, lb, volume

    def boxes_overlap(self, b1, b2):
        """
        Determines if two boxes overlap in space.
        Each box is represented as a dict with keys:
          x, y, z, dx, dy, dz.
        Returns True if the boxes overlap (i.e. intersect in all three dimensions, not just touch).
        """
        if b1['x'] + b1['dx'] - TOL <= b2['x'] or b2['x'] + b2['dx'] - TOL <= b1['x']:
            return False
        if b1['y'] + b1['dy'] - TOL <= b2['y'] or b2['y'] + b2['dy'] - TOL <= b1['y']:
            return False
        if b1['z'] + b1['dz'] - TOL <= b2['z'] or b2['z'] + b2['dz'] - TOL <= b1['z']:
            return False
        return True

    def eval_func(self, container, n, cargo_vol, box_types, instance, util, m, placements):
        """
        Hard evaluation for a container–loading solution.
        This function checks all constraints and raises an error immediately when any
        constraint is violated. The constraints include:
          - Validity of the box type index.
          - Box orientation (via get_box_dimensions).
          - Box placement completely within container boundaries.
          - Not exceeding the available counts for each box type.
          - Proper support: every box not on the floor must be fully and uniquely supported.
          - Overlap: boxes may only overlap if one is exactly supporting the other.
          - Load-bearing capacity: the weight on each box must not exceed its capacity.
        If all constraints are met, the function returns the container volume utilization,
        i.e., (total placed box volume) / (container volume).
        Inputs:
          - container: tuple (L, W, H) in cm.
          - n: number of box types.
          - cargo_vol: total cargo volume (m³) (not used in evaluation).
          - box_types: list of box type dictionaries.
          - instance: instance number (int) (not used in evaluation).
          - util: reported utilization (float) (ignored here).
          - m: number of placements.
          - placements: list of placements; each placement is a dict with keys:
                'box_type' (int, 1-indexed),
                'orientation' (int),
                'x', 'y', 'z' (floats).
        Returns:
          A float representing the container utilization if all constraints are satisfied.
        """
        TOL = 1e-6
        container_L, container_W, container_H = container
        placed = []
        usage = [0] * len(box_types)

        # Process each placement: check box type, orientation, and container boundaries.
        for idx, placement in enumerate(placements):
            bt_index = placement['box_type'] - 1
            if bt_index < 0 or bt_index >= len(box_types):
                raise ValueError(f"Invalid box type index in placement {idx}: {placement['box_type']}")

            usage[bt_index] += 1
            box = box_types[bt_index]

            try:
                # get_box_dimensions should return (dx, dy, dz, load_bearing, volume)
                dx, dy, dz, lb, volume = self.get_box_dimensions(box, placement['orientation'])
            except Exception as e:
                raise ValueError(f"Orientation error for placement {idx}: {e}")

            # Check that the box is completely inside the container.
            if (placement['x'] < -TOL or placement['y'] < -TOL or placement['z'] < -TOL or
                    placement['x'] + dx > container_L + TOL or
                    placement['y'] + dy > container_W + TOL or
                    placement['z'] + dz > container_H + TOL):
                raise ValueError(f"Box at placement {idx} is out-of-bound")

            placed.append({
                'id': idx,
                'box_type': bt_index,
                'orientation': placement['orientation'],
                'x': placement['x'],
                'y': placement['y'],
                'z': placement['z'],
                'dx': dx,
                'dy': dy,
                'dz': dz,
                'lb': lb,
                'weight': box['weight'],
                'volume': volume
            })

        # Check that the usage does not exceed available counts.
        for i, count in enumerate(usage):
            if count > box_types[i]['count']:
                raise ValueError(
                    f"Usage error: Box type {i + 1} used {count} times but only {box_types[i]['count']} available")

        # Determine support relationships.
        support_of = {}  # Maps a box's id to the id of its supporting box.
        for b in placed:
            # Boxes on the floor need no support.
            if abs(b['z']) < TOL:
                continue

            candidate = None
            for other in placed:
                if other['id'] == b['id']:
                    continue
                # Check if other box's top face aligns with the bottom of b.
                if abs(other['z'] + other['dz'] - b['z']) > TOL:
                    continue
                # b's horizontal projection must be completely inside other's top face.
                if b['x'] + TOL < other['x'] or (b['x'] + b['dx']) - TOL > other['x'] + other['dx']:
                    continue
                if b['y'] + TOL < other['y'] or (b['y'] + b['dy']) - TOL > other['y'] + other['dy']:
                    continue
                if candidate is not None:
                    raise ValueError(f"Ambiguous support for box id {b['id']} (placement {b['id']})")
                candidate = other
            if candidate is None:
                raise ValueError(f"Missing support for box id {b['id']} (placement {b['id']})")
            support_of[b['id']] = candidate['id']

        # Check for improper overlaps.
        # Overlap is allowed only if one box is exactly supporting the other.
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                b1 = placed[i]
                b2 = placed[j]
                # Skip if boxes are in non-overlapping vertical positions.
                if b1['z'] + b1['dz'] - TOL <= b2['z'] or b2['z'] + b2['dz'] - TOL <= b1['z']:
                    continue
                if self.boxes_overlap(b1, b2):
                    if support_of.get(b1['id'], -1) != b2['id'] and support_of.get(b2['id'], -1) != b1['id']:
                        raise ValueError(f"Improper overlap between box id {b1['id']} and box id {b2['id']}")

        # Compute load on each box.
        total_load = {b['id']: 0.0 for b in placed}
        placed_sorted = sorted(placed, key=lambda b: b['z'], reverse=True)
        for b in placed_sorted:
            load_here = b['weight'] + total_load[b['id']]
            if b['id'] in support_of:
                sup_id = support_of[b['id']]
                total_load[sup_id] += load_here

        # Verify load-bearing capacity for each box.
        for b in placed:
            capacity = b['dx'] * b['dy'] * b['lb']
            if total_load[b['id']] > capacity + TOL:
                excess = total_load[b['id']] - capacity
                raise ValueError(f"Load-bearing capacity exceeded for box id {b['id']}: overload {excess}")

        total_box_volume = sum(b['volume'] for b in placed)
        container_volume = container_L * container_W * container_H
        utilization = total_box_volume / container_volume if container_volume > 0 else 0.0

        return utilization

    def get_dev(self):
        dev = {
            'wtpack1.txt': [23, 24, 74, 19, 18, 98, 15, 80, 20, 44, 49, 95, 21, 64, 37, 46, 88, 29, 2, 41, 12, 56, 52,
                            31,
                            86, 92, 57, 33, 78, 26, 10, 38, 40, 32, 67, 89, 85, 7, 11, 53, 97, 22, 70, 82, 8, 48, 43,
                            45,
                            91, 71],
            'wtpack2.txt': [17, 7, 76, 44, 74, 95, 47, 53, 31, 55, 58, 50, 21, 41, 14, 98, 49, 67, 97, 88, 73, 87, 34,
                            19,
                            64, 90, 54, 82, 61, 93, 91, 75, 59, 5, 71, 8, 18, 72, 92, 85, 40, 32, 43, 42, 39, 30, 10,
                            48,
                            25, 15],
            'wtpack3.txt': [94, 25, 40, 83, 39, 80, 13, 64, 70, 21, 65, 4, 31, 54, 45, 58, 29, 33, 59, 42, 69, 92, 79,
                            96,
                            71, 43, 50, 19, 75, 89, 98, 97, 77, 72, 51, 2, 18, 93, 52, 88, 68, 56, 7, 26, 32, 46, 87,
                            91,
                            22, 49],
            'wtpack4.txt': [7, 78, 37, 44, 33, 10, 23, 14, 39, 6, 79, 36, 38, 25, 97, 88, 26, 54, 76, 51, 99, 62, 20,
                            48,
                            56, 32, 49, 2, 47, 95, 86, 22, 8, 53, 71, 85, 93, 92, 90, 0, 52, 91, 28, 84, 63, 31, 24, 11,
                            15,
                            80],
            'wtpack5.txt': [5, 56, 60, 51, 64, 17, 88, 3, 76, 37, 78, 70, 74, 30, 2, 57, 11, 34, 96, 16, 41, 4, 15, 7,
                            42,
                            65, 97, 80, 89, 69, 39, 25, 0, 32, 81, 95, 82, 19, 31, 8, 85, 94, 33, 14, 55, 93, 18, 83,
                            61,
                            87],
            'wtpack6.txt': [33, 3, 58, 46, 8, 35, 95, 64, 90, 60, 43, 11, 27, 99, 91, 30, 68, 70, 41, 96, 81, 47, 57,
                            87,
                            74, 42, 16, 66, 28, 98, 85, 4, 72, 88, 59, 75, 51, 82, 71, 14, 65, 10, 40, 0, 38, 83, 52, 7,
                            86,
                            89],
            'wtpack7.txt': [24, 94, 50, 40, 76, 58, 15, 36, 5, 1, 27, 8, 18, 87, 88, 92, 38, 54, 80, 41, 21, 46, 57, 59,
                            91,
                            51, 97, 95, 79, 4, 22, 85, 26, 53, 42, 64, 9, 83, 96, 29, 44, 89, 73, 77, 69, 72, 81, 61,
                            93,
                            2]}

        return dev


