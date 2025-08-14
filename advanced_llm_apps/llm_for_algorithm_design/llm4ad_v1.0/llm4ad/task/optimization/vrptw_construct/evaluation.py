# Module Name: VRPTWEvaluation
# Last Revision: 2025/2/16
# Description: Evaluates the Vehicle Routing Problem with Time Windows (VRPTW).
#       The VRPTW involves finding optimal routes for a fleet of vehicles to serve a set of customers, 
#       respecting time windows and vehicle capacity constraints.
#       This module is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Parameters:
#   - timeout_seconds: Maximum allowed time (in seconds) for the evaluation process: int (default: 30).
#   - problem_size: Number of customers to serve (excluding the depot): int (default: 50).
#   - n_instance: Number of problem instances to generate: int (default: 16).
# 
# References:
#   - Fei Liu, Rui Zhang, Zhuoliang Xie, Rui Sun, Kai Li, Xi Lin, Zhenkun Wang, 
#       Zhichao Lu, and Qingfu Zhang, "LLM4AD: A Platform for Algorithm Design 
#       with Large Language Model," arXiv preprint arXiv:2412.17287 (2024).
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
import copy
import numpy as np
from llm4ad.base import Evaluation
from llm4ad.task.optimization.vrptw_construct.get_instance import GetData
from llm4ad.task.optimization.vrptw_construct.template import template_program, task_description


class VRPTWEvaluation(Evaluation):
    def __init__(self,
                 timeout_seconds=30,
                 problem_size=50,
                 n_instance=16,
                 **kwargs):

        super().__init__(
            template_program=template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds
        )

        self.problem_size = problem_size
        self.n_instance = n_instance

        getData = GetData(self.n_instance, self.problem_size + 1)
        self._datasets = getData.generate_instances()

    def tour_cost(self, distance_matrix, solution, time_service, time_windows):
        cost = 0
        current_time = 0

        for j in range(len(solution) - 1):
            travel_time = distance_matrix[int(solution[j]), int(solution[j + 1])]
            # print(current_time)
            current_time += travel_time

            if current_time < time_windows[solution[j + 1]][0]:
                current_time = time_windows[solution[j + 1]][0]
            if max(current_time, time_windows[solution[j + 1]][0]) > time_windows[solution[j + 1]][1]:
                # print(max(current_time ,time_windows[solution[j + 1]][0])+time_service[solution[j + 1]] )
                # print(time_windows[solution[j + 1]][1])
                return float('inf')  # Exceeds time window
            current_time += time_service[solution[j + 1]]
            cost += travel_time
            if (solution[j + 1] == 0):
                current_time = 0
        return cost

    def evaluate_program(self, program_str: str, callable_func: callable) -> Any | None:
        return self.evaluate(callable_func)

    def evaluate(self, heuristic):
        dis = np.ones(self.n_instance)
        n_ins = 0

        for instance, distance_matrix, demands, vehicle_capacity, time_service, time_windows in self._datasets:
            route = []
            current_load = 0
            current_node = 0
            current_time = 0
            route.append(current_node)
            unvisited_nodes = set(range(1, self.problem_size + 1))  # Assuming node 0 is the depot
            all_nodes = np.array(list(unvisited_nodes))
            feasible_unvisited_nodes = all_nodes

            unvisited_nodes_depot = np.array(list(unvisited_nodes))

            while unvisited_nodes:

                next_node = heuristic(current_node,
                                      0,
                                      feasible_unvisited_nodes,
                                      vehicle_capacity - current_load,
                                      current_time,
                                      copy.deepcopy(demands),
                                      copy.deepcopy(distance_matrix),
                                      copy.deepcopy(time_windows))
                if next_node == 0:
                    route.append(next_node)
                    current_load = 0
                    current_time = 0
                    current_node = 0
                    unvisited_nodes_depot = np.array(list(unvisited_nodes))
                else:
                    travel_time = distance_matrix[current_node, next_node]
                    current_time += (travel_time)
                    current_time = max(current_time, time_windows[next_node][0])
                    current_time += time_service[next_node]
                    # if current_time < time_windows[next_node][0]:
                    #     current_time = time_windows[next_node][0]
                    # if current_time > time_windows[next_node][1]:
                    #     print(current_time)
                    #     print(time_windows[next_node][1])
                    #     return float('inf')  # Exceeds time window
                    route.append(next_node)
                    current_load += demands[next_node]
                    unvisited_nodes.remove(next_node)
                    current_node = next_node
                    unvisited_nodes_depot = np.append(np.array(list(unvisited_nodes)), 0)

                feasible_nodes_tw = np.array([node for node in all_nodes \
                                              if max(current_time + distance_matrix[current_node][node], time_windows[node][0]) < time_windows[node][1] - 0.0001 \
                                              and max(current_time + distance_matrix[current_node][node], time_windows[node][0]) + time_service[node] + distance_matrix[node][0] < time_windows[0][1] - 0.0001])
                feasible_nodes_capacity = np.array([node for node in all_nodes if current_load + demands[node] <= vehicle_capacity])
                # Determine feasible and unvisited nodes
                feasible_unvisited_nodes = np.intersect1d(np.intersect1d(feasible_nodes_tw, feasible_nodes_capacity), list(unvisited_nodes))

                if len(unvisited_nodes) > 0 and len(feasible_unvisited_nodes) < 1:
                    route.append(0)
                    current_load = 0
                    current_time = 0
                    current_node = 0
                    feasible_unvisited_nodes = np.array(list(unvisited_nodes))

            # print(set(route))

            if len(set(route)) != self.problem_size + 1:
                return None

            LLM_dis = self.tour_cost(distance_matrix, route, time_service, time_windows)
            dis[n_ins] = LLM_dis

            n_ins += 1
            if n_ins == self.n_instance:
                break
        # print(dis)
        ave_dis = np.average(dis)
        return -ave_dis


if __name__ == '__main__':
    def select_next_node(current_node: int, depot: int, unvisited_nodes: np.ndarray, rest_capacity: np.ndarray, current_time: np.ndarray, demands: np.ndarray, distance_matrix: np.ndarray, time_windows: np.ndarray) -> int:
        """Design a novel algorithm to select the next node in each step.
        Args:
            current_node: ID of the current node.
            depot: ID of the depot.
            unvisited_nodes: Array of IDs of unvisited nodes.
            rest_capacity: Rest capacity of vehicle
            current_time: Current time
            demands: Demands of nodes
            distance_matrix: Distance matrix of nodes.
            time_windows: Time windows of nodes.
        Return:
            ID of the next node to visit.
        """
        best_node = -1
        best_value = -float('inf')

        for node in unvisited_nodes:
            if demands[node] <= rest_capacity:
                travel_time = distance_matrix[current_node, node]
                arrival_time = current_time + travel_time

                if arrival_time <= time_windows[node][1]:  # Checking if within time window
                    wait_time = max(0, time_windows[node][0] - arrival_time)
                    effective_time = arrival_time + wait_time
                    distance_to_demand_ratio = travel_time / demands[node] if demands[node] > 0 else float('inf')

                    if distance_to_demand_ratio > best_value:
                        best_value = distance_to_demand_ratio
                        best_node = node

        return best_node if best_node != -1 else depot


    eval = VRPTWEvaluation()
    res = eval.evaluate_program('', select_next_node)
    print(res)
