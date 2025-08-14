# name: str: TSP_GLS_2O_Evaluation
# Parameters:
# timeout_seconds: int: 20
# end
from __future__ import annotations

from typing import Tuple, Any
import numpy as np
from llm4ad.base import Evaluation
from llm4ad.task.optimization.tsp_gls_2O.get_instance import GetData, TSPInstance
from llm4ad.task.optimization.tsp_gls_2O.template import template_program, task_description
from .gls import guided_local_search_with_time

__all__ = ['TSP_GLS_2O_Evaluation']

perturbation_moves = 5
iter_limit = 1000


def calculate_cost(inst: TSPInstance, path: np.ndarray) -> float:
    # assert (np.sort(path) == np.arange(inst.n)).all(), 'Illegal path'
    return inst.distmat[path, np.roll(path, 1)].sum().item()

def solve_with_time(inst: TSPInstance, eva) -> Tuple[float, float]:
    try:
        result, running_time = guided_local_search_with_time(inst.distmat, inst.distmat.copy(), eva, perturbation_moves, iter_limit)
        cost = calculate_cost(inst, result)
    except Exception as e:
        # cost, running_time = 1E10, 1E10
        cost, running_time = float("inf"), float("inf")
    # print(result)
    return cost, running_time

def evaluate(instance_data,n_ins,prob_size, eva: callable) -> np.ndarray:
    objs = np.zeros((n_ins, 2))

    for i in range(n_ins):
        obj = solve_with_time(instance_data[i], eva)
        # print(f'{obj[0]}, {obj[1]}')
        objs[i] = np.array(obj)

    obj = np.mean(objs, axis=0)
    return -obj


class TSP_GLS_2O_Evaluation(Evaluation):
    """Evaluator for traveling salesman problem."""

    def __init__(self, **kwargs):

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
            timeout_seconds=20
        )

        self.n_instance = 16
        self.problem_size = 100
        getData = GetData(self.n_instance, self.problem_size)
        self._datasets = getData.generate_instances()

    def evaluate_program(self, program_str: str, callable_func: callable) -> Any | None:
        return evaluate(self._datasets,self.n_instance,self.problem_size, callable_func)
    

if __name__ == '__main__':
    import numpy as np


    def update_edge_distance(edge_distance: np.ndarray, local_opt_tour: np.ndarray,
                             edge_n_used: np.ndarray) -> np.ndarray:
        """
        Design a novel algorithm to update the distance matrix.

        Args:
        edge_distance: A matrix of the distance.
        local_opt_tour: An array of the local optimal tour of IDs.
        edge_n_used: A matrix of the number of each edge used during permutation.

        Return:
        updated_edge_distance: A matrix of the updated distance.
        """
        updated_edge_distance = np.copy(edge_distance)

        # Calculate combined importance and frequency factor
        combined_factor = (1 / edge_n_used) + (1 / edge_n_used)

        for i in range(len(local_opt_tour) - 1):
            node1 = local_opt_tour[i]
            node2 = local_opt_tour[i + 1]

            update_factor = combined_factor[node1, node2]

            updated_edge_distance[node1, node2] += update_factor
            updated_edge_distance[node2, node1] = updated_edge_distance[node1, node2]

        return updated_edge_distance
    
    tsp = TSP_GLS_2O_Evaluation()
    tsp.evaluate_program('_', update_edge_distance)