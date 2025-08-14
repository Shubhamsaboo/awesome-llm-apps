template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(n: int, m: int, matrix: list) -> dict:
    """
    Solves the flow shop scheduling problem.
    Input kwargs:
      - n (int): Number of jobs.
      - m (int): Number of machines.
      - matrix (list of list of int): Processing times for each job, where each sublist
        contains m integers (processing times for machines 0 through m-1).
    Evaluation Metric:
      The solution is evaluated by its makespan, which is the completion time of the last
      job on the last machine computed by the classical flow shop recurrence.
    Returns:
      dict: A dictionary with a single key 'job_sequence' whose value is a permutation
            (1-indexed) of the job indices. For example, for 4 jobs, a valid return is:
            {'job_sequence': [1, 3, 2, 4]}
    Note: This is a placeholder implementation.
    """
    # Placeholder: simply return the identity permutation.
    return {'job_sequence': list(range(1, kwargs['n'] + 1))}
'''

task_description = ("Given  n  jobs and  m  machines, the goal of the flow shop scheduling problem is to determine "
                    "the optimal job sequence that minimizes the makespan, i.e., the total time required to complete "
                    "all jobs on all machines. Each job follows the same machine order, and the processing times are "
                    "specified in an  n \\times m  matrix. The output is a permutation of job indices representing the "
                    "processing order. If the constraints are not satisfied (e.g., invalid job sequencing), "
                    "the solution receives no score. The objective is to optimize the makespan using the classical "
                    "flow shop recurrence."
                    "Help me design a novel algorithm to solve this problem.")
