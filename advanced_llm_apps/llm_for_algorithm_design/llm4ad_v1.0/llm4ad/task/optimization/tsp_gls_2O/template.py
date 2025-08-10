template_program = '''
import numpy as np
def update_edge_distance(edge_distance: np.ndarray, local_opt_tour: np.ndarray, edge_n_used: np.ndarray) -> np.ndarray:
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
'''

task_description = "Given an edge distance matrix and a local optimal route, please help me design a strategy to update the distance matrix to avoid being trapped in the local optimum with the final goal of finding a tour with minimized distance. You should create a heuristic for me to update the edge distance matrix."

