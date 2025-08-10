# Module Name: ASPEvaluation
# Last Revision: 2025/2/14
# Description: Evaluates admissible sets for symmetric constant-weight optimization problems.
#              This module is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
# 
# Parameters:
#   - dimension: int - The dimension of the problem space (default: 15).
#   - weight: int - The weight constraint for the admissible set (default: 10).
#   - timeout_seconds: int - Maximum allowed time (in seconds) for the evaluation process (default: 60).
# 
# References:
#   - Bernardino Romera-Paredes, Mohammadamin Barekatain, Alexander Novikov, 
#     Matej Balog, M. Pawan Kumar, Emilien Dupont, Francisco JR Ruiz et al. 
#     "Mathematical discoveries from program search with large language models." 
#     Nature 625, no. 7995 (2024): 468-475.
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

import itertools
from typing import Any, List, Tuple
import numpy as np

from llm4ad.base import Evaluation
from llm4ad.task.optimization.admissible_set.template import template_program, task_description

__all__ = ['ASPEvaluation']

class ASPEvaluation(Evaluation):
    """Evaluator for online bin packing problem."""

    def __init__(self, timeout_seconds=60, dimension=15, weight=10, **kwargs):
        """
            Args:
                - 'dimension' (int): The dimension of tested case (default is 15).
                - 'weight' (int): The wight of tested case (default is 10).
        """

        super().__init__(
            template_program=template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds
        )

        self.dimension = dimension
        self.weight = weight

        
        self.TRIPLES = [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 1, 2), (0, 2, 1), (1, 1, 1), (2, 2, 2)]
        self.INT_TO_WEIGHT = [0, 1, 1, 2, 2, 3, 3]
        self.Optimal_Set_Length = {
            "n12w7": 792,
            "n15w10": 3003,
            "n21w15": 43596,
            "n24w17": 237984
        }


    def expand_admissible_set(self, pre_admissible_set: List[Tuple[int, ...]]) -> List[Tuple[int, ...]]:
        """Expands a pre-admissible set into an admissible set."""
        num_groups = len(pre_admissible_set[0])
        admissible_set_15_10 = []
        for row in pre_admissible_set:
            rotations = [[] for _ in range(num_groups)]
            for i in range(num_groups):
                x, y, z = self.TRIPLES[row[i]]
                rotations[i].append((x, y, z))
                if not x == y == z:
                    rotations[i].append((z, x, y))
                    rotations[i].append((y, z, x))
            product = list(itertools.product(*rotations))
            concatenated = [sum(xs, ()) for xs in product]
            admissible_set_15_10.extend(concatenated)
        return admissible_set_15_10


    def get_surviving_children(self, extant_elements, new_element, valid_children):
        """Returns the indices of `valid_children` that remain valid after adding `new_element` to `extant_elements`."""
        bad_triples = {(0, 0, 0), (0, 1, 1), (0, 2, 2), (0, 3, 3), (0, 4, 4), (0, 5, 5), (0, 6, 6), (1, 1, 1),
                    (1, 1, 2),
                    (1, 2, 2), (1, 2, 3), (1, 2, 4), (1, 3, 3), (1, 4, 4), (1, 5, 5), (1, 6, 6), (2, 2, 2),
                    (2, 3, 3),
                    (2, 4, 4), (2, 5, 5), (2, 6, 6), (3, 3, 3), (3, 3, 4), (3, 4, 4), (3, 4, 5), (3, 4, 6),
                    (3, 5, 5),
                    (3, 6, 6), (4, 4, 4), (4, 5, 5), (4, 6, 6), (5, 5, 5), (5, 5, 6), (5, 6, 6), (6, 6, 6)}

        # Compute.
        valid_indices = []
        for index, child in enumerate(valid_children):
            # Invalidate based on 2 elements from `new_element` and 1 element from a
            # potential child.
            if all(self.INT_TO_WEIGHT[x] <= self.INT_TO_WEIGHT[y]
                for x, y in zip(new_element, child)):
                continue
            # Invalidate based on 1 element from `new_element` and 2 elements from a
            # potential child.
            if all(self.INT_TO_WEIGHT[x] >= self.INT_TO_WEIGHT[y]
                for x, y in zip(new_element, child)):
                continue
            # Invalidate based on 1 element from `extant_elements`, 1 element from
            # `new_element`, and 1 element from a potential child.
            is_invalid = False
            for extant_element in extant_elements:
                if all(tuple(sorted((x, y, z))) in bad_triples
                    for x, y, z in zip(extant_element, new_element, child)):
                    is_invalid = True
                    break
            if is_invalid:
                continue

            valid_indices.append(index)
        return valid_indices


    def evaluate(self, priority: callable) -> int:

        """Generates a symmetric constant-weight admissible set I(n, w)."""
        num_groups = self.dimension // 3
        assert 3 * num_groups == self.dimension

        # Compute the scores of all valid (weight w) children.
        valid_children = []
        for child in itertools.product(range(7), repeat=num_groups):
            weight = sum(self.INT_TO_WEIGHT[x] for x in child)
            if weight == self.weight:
                valid_children.append(np.array(child, dtype=np.int32))

        valid_scores = np.array([
            priority(sum([self.TRIPLES[x] for x in xs], ()), self.dimension, self.weight) for xs in valid_children])

        # Greedy search guided by the scores.
        pre_admissible_set = np.empty((0, num_groups), dtype=np.int32)
        while valid_children:
            max_index = np.argmax(valid_scores)
            max_child = valid_children[max_index]
            surviving_indices = self.get_surviving_children(pre_admissible_set, max_child, valid_children)
            valid_children = [valid_children[i] for i in surviving_indices]
            valid_scores = valid_scores[surviving_indices]

            pre_admissible_set = np.concatenate([pre_admissible_set, max_child[None]], axis=0)

        admissible_set = np.array(self.expand_admissible_set(pre_admissible_set))

        return (len(admissible_set) - self.Optimal_Set_Length[f"n{self.dimension}w{self.weight}"])


    def evaluate_program(self, program_str: str, callable_func: callable) -> Any | None:
        return self.evaluate(callable_func)


if __name__ == '__main__':
    def priority(el: tuple, n: int, w: int) -> float:
        """Design a novel algorithm to evaluate a vector for potential inclusion in a set
        Args:
            el: Candidate vectors for the admissible set.
            n: Number of dimensions and the length of a vector.
            w: Weight of each vector.

        Return:
            The priorities of `el`.
        """
        priorities = sum([abs(i) for i in el]) / n
        return priorities

    eval = ASPEvaluation()
    res = eval.evaluate_program('', priority)
    print(res)
