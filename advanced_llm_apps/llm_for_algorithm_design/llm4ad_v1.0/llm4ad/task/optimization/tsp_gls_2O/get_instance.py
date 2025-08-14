import numpy as np
import numpy.typing as npt
from scipy.spatial import distance_matrix


class GetData():
    def __init__(self,n_instance,n_cities):
        self.n_instance = n_instance
        self.n_cities = n_cities

    def generate_instances(self):
        np.random.seed(2024)
        instance_data = []
        for _ in range(self.n_instance):
            coordinates = np.random.random((self.n_cities, 2))
            instance_data.append(TSPInstance(coordinates))
        return instance_data

class TSPInstance:
    def __init__(self, positions: npt.NDArray[np.float_]) -> None:
        self.positions = positions
        self.n = positions.shape[0]
        self.distmat = distance_matrix(positions, positions) + np.eye(self.n)*1e-5