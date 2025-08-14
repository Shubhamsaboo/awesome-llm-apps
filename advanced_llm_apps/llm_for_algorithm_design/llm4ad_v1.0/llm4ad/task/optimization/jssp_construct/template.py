template_program = '''
import numpy as np

def determine_next_operation(current_status, feasible_operations):
    """
    Determine the next operation to schedule based on a greedy heuristic.

    Args:
        current_status: A dictionary representing the current status of each machine and job.
        feasible_operations: A list of feasible operations that can be scheduled next.

    Returns:
        The next operation to schedule, represented as a tuple (job_id, machine_id, processing_time).
    """
    # Simple greedy heuristic: choose the operation with the shortest processing time
    next_operation = min(feasible_operations, key=lambda x: x[2])
    return next_operation
'''

task_description = '''
Given jobs and machines, schedule jobs on machines to minimize the total makespan. Design an algorithm to select the next operation in each step.
'''
