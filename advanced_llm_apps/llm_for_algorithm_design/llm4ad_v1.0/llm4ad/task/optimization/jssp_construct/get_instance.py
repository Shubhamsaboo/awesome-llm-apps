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
                job_processing_times = np.random.randint(10, 100, size=self.n_machines).tolist()
                processing_times.append(job_processing_times)

            instance_data.append((processing_times, self.n_jobs, self.n_machines))

        return instance_data
