import numpy as np


class GetData:
    def __init__(self, n_instance: int, n_jobs: int, n_machines: int):
        """
        Initialize the GetData class for JSSP.

        Args:
            n_instance: Number of instances to generate.
            n_jobs: Number of jobs.
            n_machines: Number of machines.
        """
        self.n_instance = n_instance
        self.n_jobs = n_jobs
        self.n_machines = n_machines

    def generate_instances(self):
        """
        Generate instances for the Job Shop Scheduling Problem.

        Returns:
            A list of tuples, where each tuple contains:
            - processing_times: A list of lists representing the processing times of each job on each machine.
            - n_jobs: Number of jobs.
            - n_machines: Number of machines.
        """
        np.random.seed(2024)  # Set seed for reproducibility
        instance_data = []

        for _ in range(self.n_instance):
            # Generate random processing times for each job on each machine
            # Each job has a sequence of operations, and each operation is assigned to a machine
            # For simplicity, we assume each job has exactly `n_machines` operations, one for each machine
            processing_times = []
            for _ in range(self.n_jobs):
                # Randomly assign processing times for each machine
                job_processing_times = np.random.randint(1, 100, size=self.n_machines).tolist()
                processing_times.append(job_processing_times)

            instance_data.append((processing_times, self.n_jobs, self.n_machines))

        return instance_data


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


def schedule_jobs(processing_times, n_jobs, n_machines):
    """
    Schedule jobs on machines using a greedy constructive heuristic.

    Args:
        processing_times: A list of lists representing the processing times of each job on each machine.
        n_jobs: Number of jobs.
        n_machines: Number of machines.

    Returns:
        The makespan, which is the total time required to complete all jobs.
    """
    # Initialize the current status of each machine and job
    machine_status = [0] * n_machines  # Time each machine is available
    job_status = [0] * n_jobs  # Time each job is available
    operation_sequence = [[] for _ in range(n_jobs)]  # Sequence of operations for each job

    # Initialize the list of all operations
    all_operations = []
    for job_id in range(n_jobs):
        for machine_id in range(n_machines):
            all_operations.append((job_id, machine_id, processing_times[job_id][machine_id]))

    # Schedule operations until all are completed
    while all_operations:
        # Determine feasible operations
        feasible_operations = []
        for operation in all_operations:
            job_id, machine_id, processing_time = operation
            if job_status[job_id] <= machine_status[machine_id]:
                feasible_operations.append(operation)

        if len(feasible_operations) == 0:
            next_operation = all_operations[0]
        else:
            # Determine the next operation to schedule
            next_operation = determine_next_operation({'machine_status': machine_status, 'job_status': job_status}, feasible_operations)

        # Schedule the next operation
        job_id, machine_id, processing_time = next_operation
        start_time = max(job_status[job_id], machine_status[machine_id])
        end_time = start_time + processing_time
        machine_status[machine_id] = end_time
        job_status[job_id] = end_time
        operation_sequence[job_id].append((machine_id, start_time, end_time))

        # Remove the scheduled operation from the list of all operations
        all_operations.remove(next_operation)

    # Calculate the makespan (total time required to complete all jobs)
    makespan = max(job_status)
    return makespan, operation_sequence


# Example usage
if __name__ == "__main__":
    # Generate data
    data_generator = GetData(n_instance=1, n_jobs=5, n_machines=5).generate_instances()

    for instance in data_generator:
        processing_times, n1, n2 = instance
        makespan, solution = schedule_jobs(processing_times, n1, n2)
        print(makespan)
        print(solution)
