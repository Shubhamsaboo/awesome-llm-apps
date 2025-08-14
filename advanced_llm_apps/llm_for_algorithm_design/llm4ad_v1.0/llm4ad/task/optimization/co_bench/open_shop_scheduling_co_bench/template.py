template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(n_jobs: int, n_machines: int, times: list, machines: list) -> dict:
    """
    Solves a single open shop scheduling test case.
    Input kwargs:
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
            Each start time must be a non-negative integer, and the schedule must respect the following constraint:
                (i) Non-parallel operation: Each job must be processed on only one machine at a time
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

task_description = ("The Open Shop Scheduling Problem involves scheduling a set of jobs across a set of machines with "
                    "the goal of minimizing the total completion time (makespan). Each job consists of several "
                    "operations, where each operation must be processed on a specific machine for a given duration. "
                    "Unlike other scheduling problems, the Open Shop variant has no predetermined order for "
                    "processing the operations of a job—operations can be scheduled in any order, but a job can only "
                    "be processed on one machine at a time, and a machine can only process one job at a time. This "
                    "creates a complex combinatorial optimization challenge where the scheduler must determine both "
                    "the sequence of operations for each job and the timing of each operation to minimize the overall "
                    "completion time while ensuring no resource conflicts."
                    "Help me design a novel algorithm to solve this problem.")
