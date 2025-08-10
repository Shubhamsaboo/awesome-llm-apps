template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(data: list[list[int]]) -> dict:
    """
    Partition individuals into 8 groups so that for every binary attribute the count of 1's is as evenly
    distributed across the groups as possible.
    Input kwargs:
      - data (list of list of int): A matrix where each inner list represents the binary attributes (0 or 1)
        of one individual.
    Evaluation Metric:
      For each attribute, calculate the number of 1’s in each group,
      then compute the absolute difference between each group’s count and the mean count for that attribute.
      Average these differences over all groups to obtain the attribute’s imbalance.
      The final score is the sum of these attribute imbalances across all attributes.
      A lower score indicates a more balanced partitioning.
    Returns:
      dict: A dictionary with one key 'assignment' whose value is a list of positive integers (one per individual)
            indicating the group assignment (using 1-based indexing). For example:
            { "assignment": [1, 1, 1, ...] }
    """
    # --- Placeholder solution ---
    # For this placeholder, we assign every individual to group 1.
    data = kwargs.get('data', [])
    num_individuals = len(data)
    return {'assignment': [1] * num_individuals}
'''

task_description = ("The task is to partition a set of individuals—each characterized by multiple binary "
                    "attributes—into exactly 8 groups such that the distribution of attribute values is as balanced "
                    "as possible across these groups. For each attribute, count the number of individuals with a ‘1’ "
                    "in each group. The optimization objective is to minimize the total imbalance, which is defined "
                    "as follows: for each attribute, calculate the absolute differences between the count in each "
                    "group and the mean count across all groups, take the average of these differences, and then sum "
                    "these averages over all attributes. The goal is to determine a group assignment for each "
                    "individual that achieves the lowest possible total imbalance score."
                    "Help me design a novel algorithm to solve this problem.")
