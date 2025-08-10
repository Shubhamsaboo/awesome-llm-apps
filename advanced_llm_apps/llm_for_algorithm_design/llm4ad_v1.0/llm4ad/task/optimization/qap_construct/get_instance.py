import numpy as np

class GetData:
    def __init__(self, n_instance: int, n_facilities: int):
        """
        Initialize the QAPDataGenerator class for the Quadratic Assignment Problem.

        Args:
            n_instance: Number of instances to generate.
            n_facilities: Number of facilities (and locations).
        """
        self.n_instance = n_instance
        self.n_facilities = n_facilities

    def generate_instances(self):
        """
        Generate instances for the Quadratic Assignment Problem.

        Returns:
            A list of tuples, where each tuple contains:
            - flow_matrix: A 2D numpy array representing the flow between facilities.
            - distance_matrix: A 2D numpy array representing the distance between locations.
        """
        np.random.seed(2024)  # Set seed for reproducibility
        instance_data = []

        for _ in range(self.n_instance):
            # Generate random flow and distance matrices
            flow_matrix = np.random.randint(1, 101, size=(self.n_facilities, self.n_facilities))
            distance_matrix = np.random.randint(1, 101, size=(self.n_facilities, self.n_facilities))

            # Ensure the matrices are symmetric and have zero diagonals
            flow_matrix = (flow_matrix + flow_matrix.T) // 2
            np.fill_diagonal(flow_matrix, 0)

            distance_matrix = (distance_matrix + distance_matrix.T) // 2
            np.fill_diagonal(distance_matrix, 0)

            instance_data.append((flow_matrix, distance_matrix))

        return instance_data

# Example usage:
# generator = QAPDataGenerator(n_instance=5, n_facilities=4)
# instances = generator.generate_instances()
# for flow, distance in instances:
#     print("Flow Matrix:\n", flow)
#     print("Distance Matrix:\n", distance)
