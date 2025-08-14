# References:
#   - Sun, W., Feng, S., Li, S., & Yang, Y. Co-bench: Benchmarking language
#       model agents in algorithm search for combinatorial optimization.
#       arXiv preprint arXiv:2504.04310 (2025).
#
# ------------------------------- Copyright --------------------------------
# Copyright (c) 2025 Optima Group.
#
# Permission is granted to use the LLM4AD platform for research purposes.
# All publications, software, or other works that utilize this platform
# or any part of its codebase must acknowledge the use of "LLM4AD" and
# cite the following reference:
#
# Fei Liu, Rui Zhang, Zhuoliang Xie, Rui Sun, Kai Li, Xi Lin, Zhenkun Wang,
# Zhichao Lu, and Qingfu Zhang, "LLM4AD: A Platform for Algorithm Design
# with Large Language Model," arXiv preprint arXiv:2412.17287 (2024).
#
# For inquiries regarding commercial use or licensing, please contact
# http://www.llm4ad.com/contact.html
# --------------------------------------------------------------------------

from __future__ import annotations

from typing import Any
import numpy as np
from llm4ad.base import Evaluation
from llm4ad.task.optimization.co_bench.utils import load_subdir_as_text
from llm4ad.task.optimization.co_bench.hybrid_reentrant_shop_scheduling_co_bench.template import template_program, task_description

__all__ = ['HRSSEvaluationCB']


class HRSSEvaluationCB(Evaluation):

    def __init__(self,
                 timeout_seconds=50,
                 **kwargs):

        """
            Args:
                None
            Raises:
                AttributeError: If the data key does not exist.
                FileNotFoundError: If the specified data file is not found.
        """

        super().__init__(
            template_program=template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds
        )

        # Load datasets from Hugging Face with fallback
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Hybrid Reentrant Shop Scheduling")
        self._datasets = {}
        for filename in dataset:
            # Join all text rows into a single string
            text_content = '\n'.join([row['text'] for row in dataset[filename]])
            self._datasets[filename] = text_content

    def evaluate_program(self, program_str: str, callable_func: callable, **kwargs) -> Any | None:
        return self.evaluate(callable_func)

    def evaluate(self, eva: callable) -> float | None:
        ins_cases = []
        for case_id, ins in enumerate(self._datasets.values()):
            ins_cases.append(self.load_data(ins))

        fitness_list = []
        try:
            for i in ins_cases:
                for j in i:
                    result = eva(j['n_jobs'], j['n_machines'], j['init_time'], j['setup_times'], j['processing_times'])
                    fitness = self.eval_func(j['n_jobs'], j['n_machines'], j['init_time'], j['setup_times'], j['processing_times'], result['permutation'], result['batch_assignment'])
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Reads the input string and parses one or more problem instances.
        The input is expected to have one or more instances separated by lines that contain only dashes (e.g., "-----").
        Each instance must include exactly 4 nonempty lines:
          1. Header line: "Number of jobs: X  Number of machines: Y"
          2. Initialization time: "Initialization time: Z"
          3. Setup times: "Setup times: t1 t2 ... tX"
          4. Processing times: "Processing times: p1 p2 ... pX"
        Returns:
          A list of dictionaries. Each dictionary corresponds to a problem instance and contains the keys:
             - 'n_jobs': integer
             - 'n_machines': integer
             - 'init_time': integer
             - 'setup_times': list of integers
             - 'processing_times': list of integers
        """
        import re
        cases = []
        lines = [line.strip() for line in input_string.split('\n') if line.strip() != '']

        # Split the file into separate instance blocks using a line of dashes as delimiter.
        instance_blocks = []
        current_block = []
        for line in lines:
            if re.match(r'^-+$', line):
                if current_block:
                    instance_blocks.append(current_block)
                    current_block = []
            else:
                current_block.append(line)
        if current_block:
            instance_blocks.append(current_block)

        # Process each instance block.
        for block in instance_blocks:
            if len(block) < 4:
                raise ValueError("Invalid instance format: each instance must contain at least 4 nonempty lines.")

            # Line 1: Extract number of jobs and number of machines.
            header_line = block[0]
            m_jobs = re.search(r'Number of jobs:\s*(\d+)', header_line)
            m_machines = re.search(r'Number of machines:\s*(\d+)', header_line)
            if not m_jobs or not m_machines:
                raise ValueError("Invalid header format in instance: '{}'".format(header_line))
            n_jobs = int(m_jobs.group(1))
            n_machines = int(m_machines.group(1))

            # Line 2: Initialization time.
            m_init = re.search(r'Initialization time:\s*(\d+)', block[1])
            if not m_init:
                raise ValueError("Invalid initialization time line: '{}'".format(block[1]))
            init_time = int(m_init.group(1))

            # Line 3: Setup times.
            m_setup = re.search(r'Setup times:\s*(.*)', block[2])
            if not m_setup:
                raise ValueError("Invalid setup times line: '{}'".format(block[2]))
            setup_str = m_setup.group(1).strip()
            setup_times = list(map(int, setup_str.split()))
            if len(setup_times) != n_jobs:
                raise ValueError(
                    "Number of setup times ({}) does not match number of jobs ({})".format(len(setup_times), n_jobs))

            # Line 4: Processing times.
            m_process = re.search(r'Processing times:\s*(.*)', block[3])
            if not m_process:
                raise ValueError("Invalid processing times line: '{}'".format(block[3]))
            process_str = m_process.group(1).strip()
            processing_times = list(map(int, process_str.split()))
            if len(processing_times) != n_jobs:
                raise ValueError(
                    "Number of processing times ({}) does not match number of jobs ({})".format(len(processing_times),
                                                                                                n_jobs))

            case = {
                'n_jobs': n_jobs,
                'n_machines': n_machines,
                'init_time': init_time,
                'setup_times': setup_times,
                'processing_times': processing_times
            }
            cases.append(case)

        return cases

    def eval_func(self, n_jobs, n_machines, init_time, setup_times, processing_times, permutation, batch_assignment):
        """
        1. Initialization on one of m identical primary machines:
             - Jobs are processed in natural order (1, 2, …, n_jobs) using list scheduling.
             - In this phase, each job takes 'init_time'. The machine assignment is determined
               by the list scheduling, and that assignment is used for the final main processing.
          2. Setup on the remote server:
             - Jobs are processed in the order specified by 'permutation' (a 1-indexed list).
             - A job's setup can start only after its initialization is complete and when the
               remote server is free. The setup time for job j is given as setup_times[j-1].
          3. Main processing on primary machines:
             - Each job is processed on the same primary machine that performed its initialization.
             - Within each machine, jobs are processed in the natural order (i.e., in order of their job indices).
             - The processing time for job j is given by processing_times[j-1].
        The makespan is defined as the time when the last job completes its main processing.
        Parameters:
          - n_jobs: Integer; number of jobs.
          - n_machines: Integer; number of primary machines.
          - init_time: Integer; initialization time for each job.
          - setup_times: List of integers; setup times for each job on the remote server.
          - processing_times: List of integers; processing times for each job in main processing.
          - permutation: List of integers of length n_jobs; a permutation (1-indexed) representing the order
                         in which jobs are processed on the remote server.
        Returns:
          A scalar (float or integer) representing the makespan (total completion time).
        Raises:
          ValueError: if any input constraint is not met.
        """
        import heapq

        # --- Input Validation ---
        if len(setup_times) != n_jobs:
            raise ValueError("Length of setup_times must equal n_jobs.")
        if len(processing_times) != n_jobs:
            raise ValueError("Length of processing_times must equal n_jobs.")
        if len(permutation) != n_jobs or sorted(permutation) != list(range(1, n_jobs + 1)):
            raise ValueError("permutation must be a valid permutation of the job indices 1 through n_jobs.")

        # --- Operation 1: Initialization on Primary Machines ---
        # Jobs are initialized in natural order using list scheduling.
        # We keep track of both finish time and the machine used for each job.
        op1_finish = [0] * (n_jobs + 1)  # op1_finish[j] for job j (1-indexed)
        machine_assignment = [0] * (n_jobs + 1)  # Which machine processed job j
        # Create a heap of available machines with tuples (next_available_time, machine_id)
        machine_heap = [(0, machine_id) for machine_id in range(1, n_machines + 1)]
        heapq.heapify(machine_heap)

        for job in range(1, n_jobs + 1):
            avail_time, machine_id = heapq.heappop(machine_heap)
            finish_time = avail_time + init_time
            op1_finish[job] = finish_time
            machine_assignment[job] = machine_id  # Record the machine used for initialization.
            heapq.heappush(machine_heap, (finish_time, machine_id))

        # --- Operation 2: Setup on the Remote Server ---
        op2_finish = [0] * (n_jobs + 1)  # op2_finish[j] for job j (1-indexed)
        current_time = 0
        for job in permutation:
            start_time = max(op1_finish[job], current_time)
            finish_time = start_time + setup_times[job - 1]
            op2_finish[job] = finish_time
            current_time = finish_time

        # --- Operation 3: Main Processing on Primary Machines ---
        # We now schedule the main processing on the same primary machine
        # that performed the job's initialization.
        # Group jobs per machine based on machine_assignment.
        jobs_by_machine = {machine_id: [] for machine_id in range(1, n_machines + 1)}
        for job in range(1, n_jobs + 1):
            assigned_machine = machine_assignment[job]
            jobs_by_machine[assigned_machine].append(job)
        # For each machine, sort jobs in natural order.
        for machine_id in jobs_by_machine:
            jobs_by_machine[machine_id].sort()

        op3_finish = [0] * (n_jobs + 1)
        machine_finish_times = {machine_id: 0 for machine_id in range(1, n_machines + 1)}
        for machine_id in range(1, n_machines + 1):
            current_machine_time = machine_finish_times[machine_id]
            for job in jobs_by_machine[machine_id]:
                release_time = op2_finish[job]  # Job is ready for main processing only after setup.
                start_time = max(current_machine_time, release_time)
                finish_time = start_time + processing_times[job - 1]
                op3_finish[job] = finish_time
                current_machine_time = finish_time
            machine_finish_times[machine_id] = current_machine_time

        # --- Calculate Makespan ---
        makespan = max(op3_finish) if op3_finish else 0
        return makespan

    def norm_score(self, results):
        optimal_scores = {
            'hrs-10_025.txt': [821.0, 809.5, 751.5, 814.5, 792.0, 785.5, 775.0, 801.0, 846.0, 850.5, 793.5, 899.5,
                               820.5,
                               799.0, 765.0, 822.0, 785.0, 781.5, 819.0, 758.5, 775.0, 813.5, 800.0, 809.0, 762.5,
                               796.5,
                               758.0, 769.0, 771.0, 873.5, 796.0, 854.0, 808.5, 768.0, 825.5, 770.0, 840.5, 848.0,
                               739.5,
                               813.5, 800.0, 788.5, 782.0, 826.5, 795.0, 743.5, 789.5, 839.0, 779.0, 816.0],
            'hrs-10_05.txt': [411.5, 410.0, 385.0, 386.0, 395.0, 402.5, 401.0, 371.0, 398.0, 403.5, 407.0, 396.0, 407.5,
                              376.5, 405.0, 401.5, 453.5, 408.0, 405.5, 382.5, 382.5, 386.5, 392.5, 388.5, 446.0, 417.5,
                              394.5, 372.0, 403.5, 363.0, 404.5, 392.0, 411.0, 408.0, 417.0, 377.0, 421.0, 383.0, 402.5,
                              399.0, 405.5, 414.0, 420.5, 377.0, 382.0, 404.5, 438.5, 401.5, 418.0, 414.5],
            'hrs-10_075.txt': [284.0, 267.5, 239.0, 269, 284, 274.0, 284, 286.0, 276, 278.5, 288, 308, 265.0, 291, 257,
                               278,
                               311, 277, 268.0, 290.5, 276.5, 290.0, 285.0, 298.0, 250.5, 276, 266.0, 248, 269.5, 266.0,
                               265.0, 280.5, 245.5, 265, 272.5, 320.5, 302, 268.0, 266.0, 264, 288.5, 269.5, 266, 279.0,
                               284.0, 284.5, 271, 283.0, 259.0, 257.0],
            'hrs-10_1.txt': [243, 267, 237, 250, 192, 273, 273, 226, 251, 242, 219, 269, 218, 229, 212.5, 266, 269, 223,
                             274, 232, 225.5, 271, 287, 288, 258, 205.5, 265, 251, 268, 259, 203.0, 251, 231, 218, 225,
                             252,
                             250, 246, 296, 202.5, 228, 247, 223, 290, 219.5, 192, 277, 224, 273, 222.5],
            'hrs-10_125.txt': [230, 168, 210, 264, 230, 297, 210, 260, 210, 290, 180, 268, 258, 187, 224, 192, 204, 289,
                               178, 236, 204, 257, 193, 251, 212, 183, 238, 205, 294, 236, 199, 238, 260, 255, 224, 260,
                               197, 234, 224, 243, 209, 261, 283, 216, 212, 238, 223, 281, 238, 247],
            'hrs-10_15.txt': [208, 206, 252, 272, 213, 259, 212, 230, 216, 236, 255, 178, 215, 188, 267, 204, 190, 217,
                              254,
                              193, 209, 255, 172, 228, 303, 213, 211, 233, 229, 163, 296, 230, 138, 241, 191, 236, 207,
                              269,
                              238, 279, 239, 232, 201, 237, 226, 243, 284, 213, 202, 216],
            'hrs-10_175.txt': [207, 183, 236, 222, 243, 270, 256, 234, 191, 213, 210, 282, 263, 172, 278, 216, 275, 210,
                               264, 221, 219, 261, 211, 189, 199, 207, 209, 210, 220, 270, 320, 236, 240, 205, 206, 199,
                               233, 191, 194, 260, 215, 230, 219, 191, 201, 248, 169, 216, 225, 185],
            'hrs-10_2.txt': [185, 244, 166, 252, 207, 204, 220, 175, 229, 182, 200, 264, 221, 211, 203, 229, 191, 210,
                             239,
                             202, 200, 238, 264, 255, 192, 187, 236, 224, 192, 207, 279, 229, 198, 217, 205, 259, 240,
                             228,
                             200, 234, 219, 177, 191, 241, 190, 253, 235, 216, 187, 229],
            'hrs-10_25.txt': [307, 242, 226, 208, 163, 222, 254, 209, 238, 159, 196, 230, 208, 255, 231, 218, 227, 237,
                              258,
                              241, 213, 204, 204, 257, 195, 246, 185, 128, 213, 188, 228, 231, 255, 150, 177, 220, 214,
                              197,
                              286, 226, 162, 226, 210, 189, 278, 234, 218, 237, 260, 212],
            'hrs-25_025.txt': [2009.5, 1922.0, 1972.0, 2013.5, 1945.5, 2114.5, 2054.0, 1957.0, 1986.5, 2024.5, 2034.0,
                               2118.5, 2016.5, 2043.5, 2009.5, 1933.5, 2028.5, 2050.5, 2066.5, 1997.0, 1926.0, 1933.0,
                               2066.0, 2101.5, 1977.0, 2004.5, 2068.5, 2000.0, 2027.0, 2071.5, 1986.5, 2031.0, 2041.5,
                               1992.0, 2073.0, 1940.5, 1977.0, 1892.5, 1918.0, 2071.0, 2109.5, 1949.0, 2024.0, 1955.0,
                               2077.0, 1959.0, 1902.0, 2079.0, 1975.0, 2083.0],
            'hrs-25_05.txt': [965.0, 932.5, 1021.5, 1033.0, 933.5, 998.0, 1075.0, 1022.5, 1033.5, 945.5, 1027.0, 1019.5,
                              955.0, 955.0, 1044.5, 1045.5, 983.0, 1016.0, 1024.0, 1016.5, 1062.0, 994.0, 983.5, 998.0,
                              1019.0, 1014.5, 996.0, 950.0, 1016.5, 1035.5, 968.5, 1028.5, 1067.0, 1027.0, 1047.0,
                              1012.0,
                              1052.0, 1058.0, 1019.0, 1015.5, 1035.5, 1041.0, 975.0, 1040.5, 973.0, 1009.5, 1013.0,
                              1041.0,
                              1003.0, 996.0],
            'hrs-25_075.txt': [673.5, 690.5, 666.0, 669.0, 717.5, 696.5, 674.0, 678.0, 693.0, 674.0, 664.5, 695.5,
                               733.0,
                               667.0, 690.5, 658.5, 637.5, 735.0, 624.0, 640.0, 683.5, 676.0, 672.0, 691.0, 707.5,
                               676.0,
                               644.0, 667.5, 676.0, 667.0, 690.5, 692.5, 701.0, 667.5, 699.5, 683.0, 686.5, 660.5,
                               705.5,
                               663.0, 689.0, 694.0, 674.0, 659, 664.0, 694.0, 662.5, 653.0, 708.0, 679.5],
            'hrs-25_1.txt': [585, 548, 543.5, 533, 526.5, 555.0, 535.5, 528.5, 548.0, 497, 558.5, 518, 502.5, 545.5,
                             541.0,
                             578, 519, 543, 543, 497, 524, 556, 595, 631, 476.0, 538, 556, 553.0, 517, 533, 578, 536.0,
                             619,
                             547, 576, 470.0, 554, 528, 574, 521, 574, 520.5, 523, 551, 519, 506, 510, 583, 580, 531],
            'hrs-25_125.txt': [482, 635, 491, 497, 514, 557, 576, 498, 520, 532, 472, 532, 556, 462, 498, 601, 540, 526,
                               528, 498, 458, 475, 549, 587, 589, 500, 481, 495.5, 464, 605, 576, 449, 525, 465, 541,
                               591,
                               446, 543, 477, 498, 564, 471, 488, 501, 500, 566, 541, 455, 566, 542],
            'hrs-25_15.txt': [555, 533, 546, 483, 422, 519, 442, 561, 508, 569, 510, 562, 629, 470, 441, 505, 465, 583,
                              483,
                              440, 540, 480, 577, 575, 458, 553, 535, 544, 418, 562, 557, 485, 497, 543, 555, 575, 480,
                              608,
                              632, 568, 552, 497, 544, 554, 577, 574, 481, 618, 550, 514],
            'hrs-25_175.txt': [575, 451, 442, 527, 487, 539, 486, 584, 505, 531, 472, 602, 526, 536, 488, 496, 469, 460,
                               593, 544, 523, 482, 548, 516, 631, 636, 463, 580, 437, 559, 596, 594, 539, 586, 448, 647,
                               532, 473, 581, 507, 532, 454, 654, 505, 542, 438, 463, 552, 544, 548],
            'hrs-25_2.txt': [561, 490, 586, 486, 469, 489, 569, 536, 578, 526, 527, 420, 526, 531, 498, 600, 611, 557,
                             485,
                             536, 530, 581, 519, 521, 565, 526, 482, 538, 521, 531, 538, 558, 512, 585, 558, 502, 609,
                             516,
                             566, 590, 495, 535, 613, 567, 576, 540, 627, 573, 482, 600],
            'hrs-25_25.txt': [573, 487, 528, 579, 510, 538, 582, 541, 495, 559, 454, 536, 506, 543, 569, 480, 544, 545,
                              576,
                              438, 435, 493, 472, 588, 500, 476, 593, 468, 465, 468, 497, 456, 529, 456, 572, 582, 596,
                              601,
                              479, 544, 523, 506, 504, 555, 522, 572, 496, 508, 591, 539],
            'hrs-50_025.txt': [4034.5, 3844.0, 4138.0, 4072.0, 4022.0, 4015.0, 4043.5, 4161.5, 3997.0, 3954.0, 3965.0,
                               4100.5, 3918.0, 3969.5, 4075.0, 4084.0, 3826.5, 4037.0, 4061.5, 3999.0, 4123.0, 4157.5,
                               4087.0, 4046.0, 4032.5, 3896.5, 4010.0, 4084.0, 4009.0, 3900.5, 3944.0, 3982.5, 3943.5,
                               4083.5, 3988.0, 3881.0, 3963.0, 4021.5, 4093.5, 3909.0, 3950.5, 3843.5, 3897.0, 4074.0,
                               4062.5, 4061.5, 3911.0, 4011.5, 4113.0, 3975.5],
            'hrs-50_05.txt': [2052.5, 2057.0, 2025.5, 2053.5, 1995.0, 2105.5, 2038.5, 2028.5, 2076.5, 2055.5, 2044.0,
                              1957.5, 2039.5, 2002.5, 2009.5, 2016.5, 2006.5, 2027.0, 1998.5, 1986.0, 1990.0, 2021.5,
                              2044.0, 2058.5, 2071.0, 1958.5, 2031.5, 2110.0, 2044.0, 1982.5, 2010.5, 2004.0, 2011.0,
                              2002.0, 1997.5, 2035.5, 2015.0, 2065.0, 1956.5, 1966.5, 2102.0, 2001.0, 2048.5, 2020.5,
                              2017.0, 2010.5, 1988.5, 1974.5, 1989.5, 2093.0],
            'hrs-50_075.txt': [1355.5, 1335.5, 1346.5, 1376.0, 1241.0, 1337.5, 1355.0, 1318.0, 1345.0, 1324.0, 1359.0,
                               1353.0, 1349.5, 1280.5, 1332.5, 1318.5, 1324.5, 1374.0, 1332.5, 1338.5, 1304.5, 1349.0,
                               1409.5, 1333.5, 1385.0, 1319.5, 1288.0, 1301.0, 1373.0, 1324.5, 1363.5, 1351.5, 1329.5,
                               1293.5, 1337.0, 1326.5, 1357.0, 1322.5, 1370.5, 1362.0, 1328.0, 1375.5, 1322.0, 1348.5,
                               1424.5, 1320.5, 1355.5, 1321.0, 1329.0, 1425.5],
            'hrs-50_1.txt': [1030.0, 1048, 1018.5, 1141, 1095, 1056.5, 1087.5, 1002, 983.0, 1179, 1126.5, 1075, 1118,
                             1034,
                             1088, 1009.5, 1052.5, 1115.5, 1054.5, 1114.0, 985.5, 1023.5, 1095, 1158, 1024.5, 1028,
                             1046,
                             1024, 1002.0, 1111, 1044.0, 1030.5, 1116.0, 1107.5, 1031, 986, 1063, 1100, 1070, 1041.5,
                             1064.0, 1056, 1060, 1124, 1060.5, 1030.5, 1097, 1011, 1148, 970.0],
            'hrs-50_125.txt': [1007, 1001, 996, 1037, 1021, 924, 1071, 988, 1034, 915, 1022, 959, 911, 968, 996, 1019,
                               940,
                               1016, 972, 983, 999, 1079, 1015, 947, 1025, 1053, 931, 1017, 1081, 1101, 968, 1095, 1109,
                               1011, 957, 1033, 1111, 1000, 1126, 1036, 1103, 1038, 927, 967, 922, 871, 1098, 939, 1092,
                               1188],
            'hrs-50_15.txt': [926, 1093, 906, 987, 956, 1119, 1069, 1015, 900, 1083, 1038, 1109, 990, 974, 1047, 1013,
                              989,
                              1130, 1022, 1019, 979, 952, 1067, 1056, 1097, 985, 1004, 983, 968, 1056, 932, 997, 943,
                              1135,
                              1113, 1044, 984, 1065, 978, 951, 976, 1081, 958, 971, 1053, 973, 934, 944, 1055, 1019],
            'hrs-50_175.txt': [1097, 977, 1146, 911, 960, 1072, 1047, 1067, 1127, 1033, 917, 944, 1122, 980, 989, 959,
                               1082,
                               1012, 1156, 969, 969, 898, 1043, 981, 1118, 1040, 1058, 974, 952, 951, 1033, 1160, 1071,
                               1077, 1043, 1054, 1094, 1026, 1026, 1087, 966, 1064, 993, 1035, 952, 1000, 1042, 946,
                               1105,
                               1094],
            'hrs-50_2.txt': [907, 1114, 971, 1045, 1066, 976, 1093, 1153, 1071, 943, 1018, 934, 943, 1057, 922, 1021,
                             1108,
                             909, 929, 1061, 932, 1001, 946, 1015, 1112, 1041, 1096, 1050, 1023, 1014, 970, 1017, 968,
                             1050,
                             1068, 941, 937, 994, 1046, 1009, 926, 1090, 1005, 1006, 1044, 1010, 924, 1008, 1026, 1011],
            'hrs-50_25.txt': [1040, 997, 947, 1068, 1055, 933, 911, 927, 1062, 873, 1030, 1061, 1051, 897, 1051, 970,
                              1030,
                              1088, 1046, 908, 996, 1014, 935, 1085, 1011, 929, 877, 1233, 1020, 1002, 1087, 960, 1149,
                              1076, 1040, 1002, 994, 974, 990, 1043, 1058, 990, 1074, 1118, 965, 1008, 1061, 1099, 1037,
                              1053]}

        normed = {}
        for case, (scores, error_message) in results.items():
            if case not in optimal_scores:
                continue  # Skip if there's no optimal score defined.
            optimal_list = optimal_scores[case]
            normed_scores = []
            # Compute normalized score for each index.
            for idx, score in enumerate(scores):
                if isinstance(score, (int, float)):
                    normed_scores.append(optimal_list[idx] / score)
                else:
                    normed_scores.append(score)
            normed[case] = (normed_scores, error_message)

        return normed

    def get_dev(self):
        dev = {
            'hrs-10_025.txt': [20, 21, 1, 6, 17, 48, 15, 43, 38, 28, 46, 18, 0, 31, 24, 9, 27, 8, 35, 2, 25, 22, 49, 5,
                               33],
            'hrs-10_05.txt': [34, 43, 45, 32, 31, 24, 46, 3, 22, 36, 0, 40, 25, 17, 23, 10, 21, 20, 14, 6, 48, 28, 8,
                              26,
                              1],
            'hrs-10_075.txt': [38, 41, 31, 22, 12, 13, 48, 32, 27, 16, 35, 17, 34, 6, 4, 30, 26, 42, 29, 3, 18, 5, 28,
                               20,
                               39],
            'hrs-10_1.txt': [49, 28, 14, 7, 0, 16, 18, 25, 44, 19, 40, 38, 24, 33, 12, 3, 41, 35, 46, 9, 11, 39, 29, 8,
                             5],
            'hrs-10_125.txt': [48, 40, 25, 36, 24, 20, 45, 4, 12, 17, 16, 28, 0, 11, 9, 23, 8, 6, 41, 34, 31, 35, 7, 44,
                               38],
            'hrs-10_15.txt': [11, 17, 21, 14, 0, 28, 45, 4, 20, 5, 9, 32, 29, 27, 44, 49, 15, 7, 39, 46, 36, 2, 31, 3,
                              1],
            'hrs-10_175.txt': [11, 27, 47, 10, 39, 20, 49, 34, 5, 38, 36, 22, 9, 14, 28, 33, 23, 37, 41, 45, 35, 12, 44,
                               17,
                               18],
            'hrs-10_2.txt': [34, 46, 8, 21, 6, 39, 26, 43, 4, 23, 9, 0, 35, 47, 3, 30, 24, 37, 42, 44, 7, 15, 38, 29,
                             49],
            'hrs-10_25.txt': [16, 4, 3, 45, 32, 12, 1, 17, 7, 0, 49, 47, 18, 21, 25, 42, 36, 11, 30, 48, 37, 13, 8, 15,
                              38],
            'hrs-25_025.txt': [18, 12, 13, 22, 8, 20, 44, 10, 47, 9, 48, 32, 27, 16, 7, 11, 25, 23, 14, 36, 17, 29, 21,
                               38,
                               45],
            'hrs-25_05.txt': [20, 7, 23, 8, 17, 37, 45, 38, 25, 18, 40, 35, 36, 46, 28, 16, 32, 22, 49, 31, 13, 1, 43,
                              39,
                              41],
            'hrs-25_075.txt': [6, 30, 23, 44, 15, 38, 24, 27, 5, 49, 39, 31, 45, 25, 11, 48, 4, 32, 21, 47, 46, 33, 12,
                               19,
                               29],
            'hrs-25_1.txt': [39, 0, 21, 24, 8, 40, 9, 41, 3, 34, 43, 16, 36, 26, 10, 7, 4, 25, 45, 20, 5, 11, 18, 31,
                             33],
            'hrs-25_125.txt': [1, 9, 38, 6, 49, 36, 14, 11, 25, 20, 39, 22, 7, 21, 29, 8, 43, 45, 2, 35, 40, 42, 10, 13,
                               30],
            'hrs-25_15.txt': [48, 46, 44, 23, 12, 26, 28, 33, 16, 30, 21, 4, 34, 9, 19, 47, 1, 13, 35, 6, 41, 2, 45, 14,
                              38],
            'hrs-25_175.txt': [4, 7, 46, 14, 1, 43, 18, 47, 5, 31, 12, 35, 8, 20, 37, 33, 22, 23, 16, 17, 10, 24, 15,
                               32,
                               19],
            'hrs-25_2.txt': [5, 32, 47, 29, 49, 15, 23, 26, 24, 44, 35, 3, 31, 42, 46, 14, 16, 12, 6, 17, 45, 37, 20,
                             22,
                             25],
            'hrs-25_25.txt': [48, 16, 45, 18, 17, 0, 8, 38, 44, 15, 49, 40, 19, 41, 47, 37, 3, 27, 34, 43, 12, 39, 1,
                              36,
                              6],
            'hrs-50_025.txt': [4, 12, 44, 23, 33, 28, 5, 27, 1, 24, 21, 36, 18, 26, 31, 37, 48, 35, 14, 11, 29, 30, 39,
                               34,
                               2],
            'hrs-50_05.txt': [27, 5, 43, 46, 25, 29, 9, 2, 36, 38, 0, 10, 7, 31, 24, 22, 45, 44, 14, 1, 47, 19, 34, 6,
                              35],
            'hrs-50_075.txt': [4, 16, 25, 26, 9, 1, 24, 17, 43, 47, 36, 38, 5, 44, 18, 27, 31, 2, 42, 39, 23, 41, 40,
                               46,
                               14],
            'hrs-50_1.txt': [6, 18, 30, 26, 27, 2, 28, 34, 15, 24, 44, 43, 1, 32, 17, 5, 16, 14, 7, 19, 25, 21, 38, 12,
                             48],
            'hrs-50_125.txt': [1, 19, 32, 11, 9, 12, 7, 37, 40, 30, 15, 16, 35, 8, 18, 45, 2, 21, 46, 29, 26, 14, 25, 4,
                               22],
            'hrs-50_15.txt': [49, 38, 5, 45, 27, 42, 14, 13, 16, 21, 10, 4, 48, 24, 32, 47, 15, 43, 1, 44, 31, 40, 2,
                              11,
                              19],
            'hrs-50_175.txt': [2, 26, 23, 19, 20, 17, 40, 27, 16, 29, 3, 30, 48, 49, 25, 39, 38, 35, 7, 6, 46, 15, 24,
                               13,
                               5],
            'hrs-50_2.txt': [19, 12, 24, 18, 22, 49, 7, 43, 1, 11, 33, 42, 35, 46, 25, 4, 32, 5, 3, 20, 29, 10, 37, 34,
                             15],
            'hrs-50_25.txt': [35, 24, 28, 34, 18, 20, 23, 49, 13, 9, 39, 2, 38, 22, 33, 36, 46, 1, 19, 29, 3, 21, 15,
                              12,
                              43]}

        return dev




