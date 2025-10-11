import numpy as np

def generate_weibull_dataset(num_instances, num_items, capacity_limit):
    """
    Generate a dataset of Weibull instances with the specified number of instances, items, and capacity limit.
    :param num_instances: The number of instances to generate.
    :param num_items: The number of items in each instance.
    :param capacity_limit: The capacity limit of each instance.
    :return: A dictionary containing the generated instances.
    """
    np.random.seed(2024)
    
    dataset = {}

    for i in range(num_instances):
        instance = {
            'capacity': capacity_limit,
            'num_items': num_items,
            'items': []
        }

        items = []

        # Generate random samples from Weibull(45, 3) distribution
        samples = np.random.weibull(3, num_items) * 45

        # Clip the samples at the specified limit
        samples = np.clip(samples, 1, capacity_limit)

        # Round the item sizes to the nearest integer
        sizes = np.round(samples).astype(int)

        # Add the items to the instance
        for size in sizes:
            items.append(size)

        instance['items'] = np.array(items)

        if num_items not in dataset:
            dataset[f'instance_{i}'] = instance

    return dataset