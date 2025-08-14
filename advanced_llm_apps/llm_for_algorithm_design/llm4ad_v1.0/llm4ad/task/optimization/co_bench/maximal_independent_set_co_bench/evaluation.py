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

import pathlib
import pickle
from typing import Any
import numpy as np
from llm4ad.base import Evaluation
from llm4ad.task.optimization.co_bench.utils import load_subdir_as_pickle
from llm4ad.task.optimization.co_bench.maximal_independent_set_co_bench.template import template_program, task_description

__all__ = ['MISEvaluationCB']


class MISEvaluationCB(Evaluation):

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

        # Load datasets from Hugging Face as pickle files
        pickle_data = load_subdir_as_pickle("CO-Bench/CO-Bench", "Maximal independent set", 
                                          include_subdirs=("er_test", "er_large_test"))
        
        # Organize datasets by filename (dict format preserves filenames)
        self._datasets = {}
        for subdir_name, graphs in pickle_data.items():
            for filename, graph in graphs.items():
                # Use filename as key, store metadata with graph as value
                dataset_entry = {
                    'name': filename.replace('.gpickle', ''),
                    'subdir': subdir_name,
                    'graph': graph,
                    'filename': filename
                }
                self._datasets[filename] = dataset_entry

    def evaluate_program(self, program_str: str, callable_func: callable, **kwargs) -> Any | None:
        return self.evaluate(callable_func)

    def evaluate(self, eva: callable) -> float | None:
        fitness_list = []
        try:
            for dataset_entry in self._datasets.values():
                # Each dataset entry already contains the graph and metadata
                result = eva(dataset_entry['graph'])
                fitness = self.eval_func(
                    name=dataset_entry['name'], 
                    graph=dataset_entry['graph'], 
                    mis_nodes=result['mis_nodes'], 
                    mis_size=len(result['mis_nodes'])
                )
                fitness_list.append(fitness)

            return np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Load data method for compatibility with comprehensive testing.
        Since MIS task loads pickle files directly in __init__, this method
        returns cases from the dictionary format.
        
        Args:
            input_string: Dataset content (not used, but required for interface)
            
        Returns:
            list: List of dataset entries for compatibility
        """
        # Return all dataset entries as a list for compatibility with testing
        return list(self._datasets.values())

    def eval_func(self, **kwargs):
        """
        Evaluate a Maximum Independent Set solution for correctness.
        Args:
            name (str): Name of the test case
            graph (networkx.Graph): The graph that was solved
            mis_nodes (list): List of nodes claimed to be in the maximum independent set
            mis_size (int): Claimed size of the maximum independent set
        Returns:
            actual_size (int): The actual size of the provided solution
            # dict: Evaluation results containing:
            #     - is_valid (bool): Whether the solution is a valid independent set
            #     - actual_size (int): The actual size of the provided solution
            #     - score (int): The score of the solution (0 if invalid, actual_size if valid)
            #     - error (str, optional): Error message if any constraint is violated
        """

        graph = kwargs['graph']
        mis_nodes = kwargs['mis_nodes']

        # Check if mis_nodes is a list
        if not isinstance(mis_nodes, list):
            raise Exception("mis_nodes must be a list")

        # Check if all nodes in mis_nodes exist in the graph
        node_set = set(graph.nodes())
        for node in mis_nodes:
            if node not in node_set:
                raise Exception(f"Node {node} in solution does not exist in graph")

        # Check for duplicates in mis_nodes
        if len(mis_nodes) != len(set(mis_nodes)):
            raise Exception("Duplicate nodes in solution")

        # Check if mis_size matches the length of mis_nodes
        actual_size = len(mis_nodes)

        # Most important: Check if it's an independent set (no edges between any nodes)
        for i in range(len(mis_nodes)):
            for j in range(i + 1, len(mis_nodes)):
                if graph.has_edge(mis_nodes[i], mis_nodes[j]):
                    raise Exception(f"Not an independent set: edge exists between {mis_nodes[i]} and {mis_nodes[j]}")

        return actual_size

    def norm_score(self, results):
        optimal_scores = {
            "er_large_test": [382] * 16,
            "er_test": [46] * 128,
            "er_valid": [46] * 100,
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
        dev = {'er_large_test': [1, 0, 8, 10, 6],
               'er_valid': [i for i in range(100)]}

        return dev




