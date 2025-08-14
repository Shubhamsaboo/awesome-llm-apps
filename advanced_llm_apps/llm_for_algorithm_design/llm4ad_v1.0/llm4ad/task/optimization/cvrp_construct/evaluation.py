# Module Name: CVRPEvaluation
# Last Revision: 2025/2/16
# Description: Evaluates the Capacitated Vehicle Routing Problem (CVRP).
#              Given a set of customers and a fleet of vehicles with limited capacity,
#              the goal is to find optimal routes for the vehicles to serve all customers
#              while minimizing the total travel distance.
#              This module is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Parameters:
#    - timeout_seconds: Maximum allowed time (in seconds) for the evaluation process: int (default: 20).
#    - n_instance: Number of problem instances to generate: int (default: 16).
#    - problem_size: Number of customers to serve: int (default: 50).
#    - capacity: Maximum capacity of each vehicle: int (default: 40).
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

import copy
from typing import Any
import matplotlib.pyplot as plt
import numpy as np

from llm4ad.base import Evaluation
from llm4ad.task.optimization.cvrp_construct.get_instance import GetData
from llm4ad.task.optimization.cvrp_construct.template import template_program, task_description


class CVRPEvaluation(Evaluation):
    def __init__(self,
                 timeout_seconds=20,
                 n_instance=16,
                 problem_size=50,
                 capacity=40,
                 **kwargs):

        super().__init__(
            template_program=template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds
        )

        self.problem_size = problem_size + 1
        self.n_instance = n_instance
        self.capacity = capacity

        getData = GetData(self.n_instance, self.problem_size, self.capacity)
        self._datasets = getData.generate_instances()

    def plot_solution(self, instance: np.ndarray, route: list, demands: list, vehicle_capacity: int):
        """
        Plot the solution of the Capacitated Vehicle Routing Problem (CVRP).

        Args:
            instance: A 2D array of node coordinates (including the depot).
            route: A list representing the sequence of nodes visited in the route.
            demands: A list of demands for each node.
            vehicle_capacity: The capacity of the vehicle.
        """
        # Extract coordinates
        x = instance[:, 0]
        y = instance[:, 1]

        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(10, 8))

        # Plot depot (node 0)
        ax.plot(x[0], y[0], 'ro', markersize=10, label='Depot')
        ax.text(x[0], y[0], 'Depot', ha='center', va='bottom', fontsize=12)

        # Plot customer nodes
        for i in range(1, len(x)):
            ax.plot(x[i], y[i], 'bo', markersize=8)
            ax.text(x[i], y[i], f'C{i}\nDem: {demands[i]}', ha='center', va='bottom', fontsize=8)

        # Split the route into individual vehicle routes based on depot visits
        routes = []
        current_route = []
        for node in route:
            current_route.append(node)
            if node == 0 and len(current_route) > 1:  # End of a route (return to depot)
                routes.append(current_route)
                current_route = [0]  # Start a new route from the depot
        if current_route:  # Add the last route if it exists
            routes.append(current_route)

        # Plot each route in a different color
        colors = plt.cm.tab10.colors  # Use a colormap for distinct colors
        for i, r in enumerate(routes):
            color = colors[i % len(colors)]  # Cycle through colors
            for j in range(len(r) - 1):
                start_node = r[j]
                end_node = r[j + 1]
                ax.plot([x[start_node], x[end_node]], [y[start_node], y[end_node]], color=color, linestyle='--', linewidth=1, label=f'Route {i + 1}' if j == 0 else None)

                # Add load information
                if end_node != 0:  # If not returning to the depot
                    ax.text((x[start_node] + x[end_node]) / 2, (y[start_node] + y[end_node]) / 2,
                            f'Load: {sum(demands[r[:j + 1]])}', ha='center', va='center', fontsize=8, rotation=45)

            # Mark start and end nodes of the route with triangles (excluding depot)
            if len(r) > 1:
                ax.plot(x[r[1]], y[r[1]], '^', color=color, markersize=10, label='Start' if i == 0 else None)  # Start node
                ax.plot(x[r[-2]], y[r[-2]], 'v', color=color, markersize=10, label='End' if i == 0 else None)  # End node

        # Set axis labels and title
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.set_title('Capacitated Vehicle Routing Problem (CVRP) Solution')
        ax.legend(loc='upper right')

        # Show the plot
        plt.tight_layout()
        plt.show()

    def tour_cost(self, instance, solution):
        cost = 0
        for j in range(len(solution) - 1):
            cost += np.linalg.norm(instance[int(solution[j])] - instance[int(solution[j + 1])])
        cost += np.linalg.norm(instance[int(solution[-1])] - instance[int(solution[0])])
        return cost

    def route_construct(self, distance_matrix, demands, vehicle_capacity, heuristic):
        route = []
        current_load = 0
        current_node = 0
        route.append(current_node)

        unvisited_nodes = set(range(1, self.problem_size))  # Assuming node 0 is the depot
        all_nodes = np.array(list(unvisited_nodes))
        feasible_unvisited_nodes = all_nodes

        while unvisited_nodes:
            next_node = heuristic(current_node,
                                  0,
                                  feasible_unvisited_nodes,  # copy
                                  vehicle_capacity - current_load,
                                  copy.deepcopy(demands),  # copy
                                  copy.deepcopy(distance_matrix))  # copy
            if next_node == 0:
                # Update route and load
                route.append(next_node)
                current_load = 0
                current_node = 0
            else:
                # Update route and load
                route.append(next_node)
                current_load += demands[next_node]
                unvisited_nodes.remove(next_node)
                current_node = next_node

            feasible_nodes_capacity = np.array([node for node in all_nodes if current_load + demands[node] <= vehicle_capacity])
            # Determine feasible and unvisited nodes
            feasible_unvisited_nodes = np.intersect1d(feasible_nodes_capacity, list(unvisited_nodes))

            if len(unvisited_nodes) > 0 and len(feasible_unvisited_nodes) < 1:
                route.append(0)
                current_load = 0
                current_node = 0
                feasible_unvisited_nodes = np.array(list(unvisited_nodes))

        # check if not all nodes have been visited 
        independent_values = set(route)
        if len(independent_values) != self.problem_size:
            return None
        return route

    def evaluate(self, heuristic):
        dis = np.ones(self.n_instance)
        n_ins = 0

        for instance, distance_matrix, demands, vehicle_capacity in self._datasets:
            route = self.route_construct(distance_matrix, demands, vehicle_capacity, heuristic)
            LLM_dis = self.tour_cost(instance, route)
            dis[n_ins] = LLM_dis
            n_ins += 1
            if n_ins == self.n_instance:
                break

        ave_dis = np.average(dis)
        return -ave_dis

    def evaluate_program(self, program_str: str, callable_func: callable) -> Any | None:
        return self.evaluate(callable_func)


if __name__ == '__main__':
    def select_next_node(current_node: int, depot: int, unvisited_nodes: np.ndarray, rest_capacity: np.ndarray, demands: np.ndarray, distance_matrix: np.ndarray) -> int:
        """Design a novel algorithm to select the next node in each step.
        Args:
            current_node: ID of the current node.
            depot: ID of the depot.
            unvisited_nodes: Array of IDs of unvisited nodes.
            rest_capacity: rest capacity of vehicle
            demands: demands of nodes
            distance_matrix: Distance matrix of nodes.
        Return:
            ID of the next node to visit.
        """
        next_node = unvisited_nodes[0]
        return next_node


    # def select_next_node(current_node: int, depot: int, unvisited_nodes: np.ndarray, rest_capacity: np.ndarray, demands: np.ndarray, distance_matrix: np.ndarray) -> int:
    #     """Design a novel algorithm to select the next node in each step.
    #     Args:
    #         current_node: ID of the current node.
    #         depot: ID of the depot.
    #         unvisited_nodes: Array of IDs of unvisited nodes.
    #         rest_capacity: rest capacity of vehicle
    #         demands: demands of nodes
    #         distance_matrix: Distance matrix of nodes.
    #     Return:
    #         ID of the next node to visit.
    #     """
    #     best_score = -1
    #     next_node = -1

    #     for node in unvisited_nodes:
    #         demand = demands[node]
    #         distance = distance_matrix[current_node][node]

    #         if demand <= rest_capacity:
    #             score = demand / distance if distance > 0 else float('inf')  # Avoid division by zero
    #             if score > best_score:
    #                 best_score = score
    #                 next_node = node

    #     return next_node

    eval = CVRPEvaluation()
    res = eval.evaluate_program('', select_next_node)
    print(res)
