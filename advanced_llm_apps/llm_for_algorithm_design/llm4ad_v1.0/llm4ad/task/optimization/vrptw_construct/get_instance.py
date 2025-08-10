import pickle

import numpy as np


class GetData:
    def __init__(self, n_instance, n_cities):
        self.n_instance = n_instance
        self.n_cities = n_cities
        self.max_time = 4.6

    def generate_instances(self):
        """each instance -> (coordinates, distances, demands, capacity)"""
        np.random.seed(2024)
        instance_data = []
        for _ in range(self.n_instance):
            coordinates = np.random.rand(self.n_cities + 1, 2)
            demands = np.append(np.array([0]), np.random.randint(1, 10, size=self.n_cities))
            capacity = 40
            distances = np.linalg.norm(coordinates[:, np.newaxis] - coordinates, axis=2)
            node_serviceTime = np.random.rand(self.n_cities) * 0.05 + 0.15
            serviceTime = np.append(np.array([0]), node_serviceTime)
            # shape: (batch, problem)
            # range: (0.15, 0.2) for T=4.6

            node_lengthTW = np.random.rand(self.n_cities) * 0.05 + 0.15
            # shape: (batch, problem)
            # range: (0.15, 0.2) for T=4.6

            d0i = distances[0][1:]
            # shape: (batch, problem)

            # ei = (np.random.rand(self.n_cities) * ((self.max_time - node_serviceTime - node_lengthTW) / d0i - 1) + 1)
            ei = np.random.rand(self.n_cities) * (((4.6 * np.ones(self.n_cities) - node_serviceTime - node_lengthTW) / d0i - 1) - 1) + 1
            # shape: (batch, problem)
            # default velocity = 1.0

            # Element-wise multiplication
            node_earlyTW = np.multiply(ei, d0i)
            # node_earlyTW = ei * d0i
            # shape: (batch, problem)
            # default velocity = 1.0

            node_lateTW = node_earlyTW + node_lengthTW
            # shape: (batch, problem)

            time_windows_node = np.append(np.array([node_earlyTW]).reshape(self.n_cities, 1), np.array([node_lateTW]).reshape(self.n_cities, 1), axis=1)

            time_windows = np.append(np.array([[0, self.max_time]]), time_windows_node, axis=0)

            instance_data.append((coordinates, distances, demands, capacity, serviceTime, time_windows))
        return instance_data


if __name__ == '__main__':
    gd = GetData(10, 50)
    data = gd.generate_instances()
    with open('data_vrptw.pkl', 'wb') as f:
        pickle.dump(data, f)
    with open('data_vrptw.pkl', 'rb') as f:
        data = pickle.load(f)
    coordinates, distances, demands, capacity, serviceTime, time_windows = data[0]
    print(time_windows)
    print(time_windows[0])
