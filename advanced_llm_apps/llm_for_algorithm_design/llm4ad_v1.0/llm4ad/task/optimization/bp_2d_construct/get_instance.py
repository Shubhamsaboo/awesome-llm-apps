import numpy as np


class GetData:
    def __init__(self, n_instance: int, n_items: int, bin_width: int, bin_height: int):
        """
        Initialize the GetData class for the 2D Bin Packing Problem.

        Args:
            n_instance: Number of instances to generate.
            n_items: Number of items.
            bin_width: Width of each bin.
            bin_height: Height of each bin.
        """
        self.n_instance = n_instance
        self.n_items = n_items
        self.bin_width = bin_width
        self.bin_height = bin_height

    def generate_instances(self):
        """
        Generate instances for the 2D Bin Packing Problem.

        Returns:
            A list of tuples, where each tuple contains:
            - item_dimensions: A list of tuples, where each tuple represents the (width, height) of an item.
            - bin_dimensions: A tuple representing the (width, height) of the bin.
        """
        np.random.seed(2024)  # Set seed for reproducibility
        instance_data = []

        for _ in range(self.n_instance):
            # Generate random item dimensions, ensuring no item exceeds the bin dimensions
            item_widths = np.random.randint(10, self.bin_width - 10, size=self.n_items)
            item_heights = np.random.randint(10, self.bin_height - 10, size=self.n_items)
            item_dimensions = list(zip(item_widths, item_heights))
            bin_dimensions = (self.bin_width, self.bin_height)
            instance_data.append((item_dimensions, bin_dimensions))

        return instance_data
