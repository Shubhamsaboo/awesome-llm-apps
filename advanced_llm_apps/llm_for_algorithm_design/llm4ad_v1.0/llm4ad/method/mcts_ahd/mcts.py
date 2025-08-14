# Module Name: MCTS_AHD
# Last Revision: 2025/7/22
# This file is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Reference:
#   - Zheng, Z., Xie, Z., Wang, Z., & Hooi, B. (2025). Monte carlo tree search for
#       comprehensive exploration in llm-based automatic heuristic design. (ICML). 2024.
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
import math


class MCTSNode:
    def __init__(self, algorithm, code, obj, depth=0, individual=None, is_root=False, parent=None, visit=0,
                 raw_info=None, Q=0):
        self.algorithm = algorithm
        self.code = code
        self.parent = parent
        self.depth = depth
        self.individual = individual
        self.children = []
        self.visits = visit
        self.subtree = []
        self.raw_info = raw_info
        self.Q = Q
        self.reward = -1 * obj

    def add_child(self, child_node: MCTSNode):
        self.children.append(child_node)


class MCTS:
    def __init__(self, root_answer, alpha, lambad0):
        self.exploration_constant_0 = lambad0  # Paramter \lambda_0
        self.alpha = alpha  # Paramter \alpha
        self.max_depth = 10
        self.epsilon = 1e-10
        self.discount_factor = 1  # constant as 1
        self.q_min = 0
        self.q_max = -10000
        self.rank_list = []

        self.root = MCTSNode(algorithm=root_answer, code=root_answer, depth=0, obj=0, is_root=True)

        # Logs
        self.critiques = []
        self.refinements = []
        self.rewards = []
        self.selected_nodes = []

    def backpropagate(self, node: MCTSNode):
        if node.Q not in self.rank_list:
            self.rank_list.append(node.Q)
            self.rank_list.sort()
        self.q_min = min(self.q_min, node.Q)
        self.q_max = max(self.q_max, node.Q)
        parent = node.parent
        while parent:
            best_child_Q = max(child.Q for child in parent.children)
            parent.Q = parent.Q * (1 - self.discount_factor) + best_child_Q * self.discount_factor
            parent.visits += 1
            if parent.code != 'Root' and parent.parent.code == 'Root':
                parent.subtree.append(node)
            parent = parent.parent

    def uct(self, node: MCTSNode, eval_remain):
        self.exploration_constant = (self.exploration_constant_0) * eval_remain
        return (node.Q - self.q_min) / (self.q_max - self.q_min) + self.exploration_constant * math.sqrt(
            math.log(node.parent.visits + 1) / node.visits
        )

    def is_fully_expanded(self, node: MCTSNode):
        return len(node.children) >= self.max_children or any(
            child.Q > node.Q for child in node.children
        ) or node.code == 'Root'
