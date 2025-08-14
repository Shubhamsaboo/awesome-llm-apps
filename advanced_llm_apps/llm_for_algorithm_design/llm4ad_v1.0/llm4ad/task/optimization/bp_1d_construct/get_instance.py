import numpy as np


class GetData:
    def __init__(self, n_instance: int, n_items: int, bin_capacity: int):
        """
        Initialize the GetData class for the 1D Bin Packing Problem.

        Args:
            n_instance: Number of instances to generate.
            n_items: Number of items.
            bin_capacity: Capacity of each bin.
        """
        self.n_instance = n_instance
        self.n_items = n_items
        self.bin_capacity = bin_capacity

    def generate_instances(self):
        """
        Generate instances for the 1D Bin Packing Problem.

        Returns:
            A list of tuples, where each tuple contains:
            - item_weights: A list of item weights.
            - bin_capacity: The capacity of each bin.
        """
        np.random.seed(2024)  # Set seed for reproducibility
        instance_data = []

        for _ in range(self.n_instance):
            # Parameters for the beta distribution
            alpha = 2  # Shape parameter (adjust as needed)
            beta = 5  # Shape parameter (adjust as needed)

            # Generate random item weights using a beta distribution
            # Scale and shift the values to the range [5, 50]
            item_weights = (50 - np.random.beta(alpha, beta, size=self.n_items) * 40).astype(int).tolist()
            # # Generate random item weights, ensuring no item exceeds the bin capacity
            # item_weights = np.random.randint(2, 9, size=self.n_items).tolist()

            # # Randomly decide for each item whether to multiply by 5 or 8
            # multipliers = np.random.choice([5, 11], size=self.n_items)

            # # Apply the multipliers to the item weights
            # modified_weights = [weight * multiplier for weight, multiplier in zip(item_weights, multipliers)]

            instance_data.append((item_weights, self.bin_capacity))

        return instance_data

# # Example usage:
# data_generator = GetData(n_instance=5, n_items=10, bin_capacity=100)
# instances = data_generator.generate_instances()
# for instance in instances:
#     print(instance)
