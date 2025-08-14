import numpy as np


class GetData:
    def __init__(self, n_instance: int, n_elements: int, n_subsets: int, max_subset_size: int):
        """
        Initialize the GetData class for the Set Covering Problem.

        Args:
            n_instance: Number of instances to generate.
            n_elements: Number of elements in the universal set.
            n_subsets: Number of subsets in the collection.
            max_subset_size: Maximum size of each subset.
        """
        self.n_instance = n_instance
        self.n_elements = n_elements
        self.n_subsets = n_subsets
        self.max_subset_size = max_subset_size

    def generate_instances(self):
        """
        Generate instances for the Set Covering Problem.

        Returns:
            A list of tuples, where each tuple contains:
            - universal_set: A list of elements in the universal set.
            - subsets: A list of subsets, where each subset is a list of elements.
        """
        np.random.seed(2024)  # Set seed for reproducibility
        instance_data = []

        for _ in range(self.n_instance):
            # Define the universal set
            universal_set = list(range(1, self.n_elements + 1))

            # Generate subsets
            subsets = []
            for _ in range(self.n_subsets):
                subset_size = np.random.randint(1, self.max_subset_size + 1)  # Random subset size
                subset = np.random.choice(universal_set, size=subset_size, replace=False).tolist()
                subsets.append(subset)

            instance_data.append((universal_set, subsets))

        return instance_data

# # Example usage:
# data_generator = GetData(n_instance=3, n_elements=10, n_subsets=5, max_subset_size=5)
# instances = data_generator.generate_instances()
# for universal_set, subsets in instances:
#     print("Universal Set:", universal_set)
#     print("Subsets:", subsets)
#     print()
