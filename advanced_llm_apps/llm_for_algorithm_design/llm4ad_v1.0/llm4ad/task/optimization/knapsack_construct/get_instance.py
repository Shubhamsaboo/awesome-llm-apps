import numpy as np


class GetData:
    def __init__(self, n_instance: int, n_items: int, knapsack_capacity: int):
        """
        Initialize the GetData class for the Knapsack Problem.

        Args:
            n_instance: Number of instances to generate.
            n_items: Number of items.
            knapsack_capacity: Capacity of the knapsack.
        """
        self.n_instance = n_instance
        self.n_items = n_items
        self.knapsack_capacity = knapsack_capacity

    def generate_instances(self):
        """
        Generate instances for the Knapsack Problem.

        Returns:
            A list of tuples, where each tuple contains:
            - item_weights: A list of item weights.
            - item_values: A list of item values.
            - knapsack_capacity: The capacity of the knapsack.
        """
        np.random.seed(2024)  # Set seed for reproducibility
        instance_data = []

        for _ in range(self.n_instance):
            # Generate random item weights, ensuring no item exceeds the knapsack capacity
            item_weights = np.random.randint(10, self.knapsack_capacity / 2 + 10, size=self.n_items).tolist()

            # Generate random item values, ensuring they are positive
            item_values = np.random.randint(1, 101, size=self.n_items).tolist()  # Values between 1 and 100

            # Append the instance data as a tuple (weights, values, capacity)
            instance_data.append((item_weights, item_values, self.knapsack_capacity))

        return instance_data
