import numpy as np


class GetData():
    def __init__(self, n_instance, n_cities):
        self.n_instance = n_instance
        self.n_cities = n_cities

    def generate_instances(self):
        np.random.seed(2024)
        instance_data = []
        for _ in range(self.n_instance):
            coordinates = np.random.rand(self.n_cities, 2)
            distances = np.linalg.norm(coordinates[:, np.newaxis] - coordinates, axis=2)
            instance_data.append((coordinates, distances))
        return instance_data
