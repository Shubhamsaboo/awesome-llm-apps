template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(n_jobs: int, n_machines: int, times: list, machines: list) -> dict:
    """
    Solves a single job shop scheduling test case.
    Input:
        - n_jobs (int): Number of jobs.
        - n_machines (int): Number of machines (and operations per job).
        - times (list of list of int): A 2D list of processing times for each operation.
          Dimensions: n_jobs x n_machines.
        - machines (list of list of int): A 2D list specifying the machine assignment for each operation.
          Dimensions: n_jobs x n_machines. Note machine is 1-indexed.
    Output:
        solution (dict): A dictionary containing:
            - start_times (list of list of int): A 2D list of start times for each operation.
              Dimensions: n_jobs x n_machines.
            Each start time must be a non-negative integer, and the schedule must respect the following constraints:
                (i) Sequential processing: For each job, an operation cannot start until its preceding operation has finished.
                (ii) Machine exclusivity: For operations assigned to the same machine, their processing intervals must not overlap.
            The evaluation function will use the start_times to compute the makespan and verify the constraints.
    """

    # Extract the case parameters
    n_jobs = kwargs["n_jobs"]
    n_machines = kwargs["n_machines"]
    times = kwargs["times"]
    machines = kwargs["machines"]

    # TODO: Implement the scheduling algorithm here.
    # For now, we provide a dummy solution where all operations start at time 0.

    # Create a start_times list with dimensions n_jobs x n_machines, initializing all start times to 0.
    start_times = [[0 for _ in range(n_machines)] for _ in range(n_jobs)]

    # Build the solution dictionary.
    solution = {"start_times": start_times}

    return solution
'''

task_description = ("The job shop scheduling problem requires assigning non-negative integer start times to a set of "
                    "operations, structured into multiple jobs, each composed of sequential operations. Each "
                    "operation is processed on a specific machine for a given processing time. The optimization goal "
                    "is to minimize the makespan, defined as the maximum completion time across all jobs. Constraints "
                    "include (i) sequential processing of operations within each job, meaning each operation cannot "
                    "start before its preceding operation finishes, and (ii) non-overlapping scheduling of operations "
                    "on the same machine. If these constraints are violated, the solution receives no score."
                    "Help me design a novel algorithm to solve this problem.")
