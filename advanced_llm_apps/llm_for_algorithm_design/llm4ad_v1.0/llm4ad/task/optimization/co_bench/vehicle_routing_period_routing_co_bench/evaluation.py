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

import ast
from typing import Any
import numpy as np
from llm4ad.base import Evaluation
from llm4ad.task.optimization.co_bench.utils import load_subdir_as_text
from llm4ad.task.optimization.co_bench.vehicle_routing_period_routing_co_bench.template import template_program, task_description

__all__ = ['VRPREvaluationCB']


class VRPREvaluationCB(Evaluation):

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

        # Load datasets from Hugging Face
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Vehicle routing: period routing")
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
                    result = eva(j['depot'], j['costumers'], j['vehicles_per_day'], j['vehicle_capacity'], j['period_length'])
                    fitness = self.eval_func(depot=j['depot'], customers=j['costumers'], vehicles_per_day=j['vehicles_per_day'], vehicle_capacity=j['vehicle_capacity'], period_length=j['period_length'], selected_schedules=result['selected_schedules'], tours=result['tours'])
                    fitness_list.append(fitness)

            return -np.mean(fitness_list)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_string):
        """
        Reads a period vehicle routing problem file and returns a dictionary with the problem data.
        The file is expected to have the following format:
          Line 1: Two integers: <num_customers> <period_length>
                  (Note: the depot is specified as customer_id = 0.)
          Line 2: A list of period_length integers representing the number of vehicles on each day.
          Line 3: A single number representing the constant capacity of every vehicle.
          Lines 4 onward: Each line represents a vertex (depot or customer) in the format:
                            customer_id x_coordinate y_coordinate demand possible_schedule_list
                            For the depot (customer_id = 0) the demand and schedule are omitted or ignored.
                            e.g., depot line: 0 30 40 0
                                  customer line: 1 37 52 7 [[1, 0], [0, 1]]
        Parameters:
          input_string (str): The input content as string.
        Returns:
          A dictionary with keys:
              - "period_length" (int)
              - "vehicles_per_day" (list of ints)
              - "vehicle_capacity" (number)
              - "depot": dict with keys: "id", "x", "y"
              - "customers": list of customer dictionaries (for customer id ≠ 0)
                          Each customer dictionary contains keys:
                              "id": int, the customer id.
                              "x": float, the x coordinate.
                              "y": float, the y coordinate.
                              "demand": float, the customer demand.
                              "schedules": list of lists, each sub-list is a binary schedule for the period.
        """

        # Read file and filter out any empty lines.
        all_lines = [line.strip() for line in input_string.split('\n')]

        # Check that we have at least 3 lines for headers.
        if len(all_lines) < 3:
            raise ValueError("Insufficient data in the file. Expect at least three header lines.")

        # Parse header
        # First line: number of customers and period length:
        header1 = all_lines[0].split()
        if len(header1) != 2:
            print(header1)
            raise ValueError("The first line must have exactly 2 tokens: <num_customers> <period_length>.")
        try:
            num_customers = int(header1[0])
            period_length = int(header1[1])
        except Exception as e:
            raise ValueError("Error parsing the number of customers or period length.") from e

        # Second line: number of vehicles on each day
        vehicles_tokens = all_lines[1].split()
        if len(vehicles_tokens) != period_length:
            raise ValueError("The number of vehicle counts provided does not equal the period length.")
        try:
            vehicles_per_day = [int(x) for x in vehicles_tokens]
        except Exception as e:
            raise ValueError("Error parsing the vehicles per day.") from e

        # Third line: vehicle capacity (all vehicles have same capacity)
        try:
            vehicle_capacity = float(all_lines[2])
        except Exception as e:
            raise ValueError("Error parsing vehicle capacity.") from e

        depot = None
        customers = []
        # Process the remaining lines.
        for line in all_lines[3:]:
            # Split into at most five tokens; the first four are assumed to be id, x, y and demand.
            parts = line.split(maxsplit=4)
            if len(parts) < 3:
                continue  # Skip lines that do not have minimum required data.

            try:
                cid = int(parts[0])
                x = float(parts[1])
                y = float(parts[2])
            except Exception as ex:
                raise ValueError("Error parsing id or coordinates in line: " + line) from ex

            # Check for depot (id == 0). For depot, we ignore demand and schedule.
            if cid == 0:
                depot = {"id": cid, "x": x, "y": y}
                # Skip further processing of demand/schedules for the depot.
                continue

            # For a customer, we expect a demand value.
            if len(parts) < 4:
                raise ValueError("Insufficient data for customer (id=%s) in line: %s" % (cid, line))
            try:
                demand = float(parts[3])
            except Exception as ex:
                raise ValueError("Error parsing demand for customer (id=%s) in line: %s" % (cid, line)) from ex

            # Parse possible schedule if provided.
            schedules = []
            if len(parts) == 5:
                try:
                    schedules = ast.literal_eval(parts[4])
                except Exception as ex:
                    raise ValueError("Error parsing delivery schedules in line: " + line) from ex

            customers.append({
                "id": cid,
                "x": x,
                "y": y,
                "demand": demand,
                "schedules": schedules
            })

        # Optionally, you can check if depot was found.
        if depot is None:
            raise ValueError("Depot (customer id 0) was not found in the file.")

        return [{
            "period_length": period_length,
            "vehicles_per_day": vehicles_per_day,
            "vehicle_capacity": vehicle_capacity,
            "depot": depot,
            "customers": customers
        }]

    def eval_func(self, **kwargs):
        """
        Evaluates the solution of the Period Vehicle Routing Problem for a single case.
        Input kwargs should include:
          - from data:
                "depot": dict with keys "id", "x", "y".
                "customers": list of customer dictionaries (each with keys "id", "x", "y", "demand", "schedules").
                "vehicles_per_day": list of ints (indicating the number of available vehicles per day).
                "vehicle_capacity": numeric, the capacity of each vehicle.
                "period_length": int, the number of days.
          - from solve:
                "selected_schedules": a mapping from customer id to the chosen schedule (a list of binary integers).
                "tours": a mapping from day (1-indexed) to a list of tours;
                         each tour is a list of vertex ids (integers), starting and ending at depot (id 0),
                         with no intermediate depot visits.
        The evaluator checks the following:
          1. For each customer (other than the depot), verifies that there is a chosen schedule,
             and that the chosen schedule is one of that customer's candidate schedules.
          2. For each day:
               - Verifies that the number of tours does not exceed the available vehicles for that day.
               - Checks that every customer whose chosen schedule requires service is visited exactly once.
          3. Each tour must:
               - Start at the depot (id 0) and end at the depot (id 0).
               - Not include any depot visit in the middle (the depot may appear only as the first and the last vertex).
               - Not visit the same customer more than once.
          4. Each tour must satisfy the capacity constraint: the total customer demand on the tour does not exceed vehicle_capacity.
          5. Finally, the evaluator computes the total tour length (using Euclidean distance) over all days.
        Returns:
          A numeric value representing the total tour length computed from the solution.
        Raises an error if any constraint is violated.
        """
        import math

        depot = kwargs["depot"]
        customers = kwargs["customers"]
        vehicles_per_day = kwargs["vehicles_per_day"]
        vehicle_capacity = kwargs["vehicle_capacity"]
        period_length = kwargs["period_length"]

        # Build a lookup table for customers by id.
        customer_lookup = {cust["id"]: cust for cust in customers}

        # Validate the selected schedules.
        selected_schedules = kwargs.get("selected_schedules")
        if not isinstance(selected_schedules, dict):
            raise ValueError("Solution must include a dictionary 'selected_schedules'.")

        # Ensure that every customer (except the depot) has a selected schedule.
        for cust in customers:
            # Assuming depot has id 0.
            if cust["id"] == 0:
                continue
            if cust["id"] not in selected_schedules:
                raise ValueError(f"Missing selected schedule for customer {cust['id']}.")

        # Now validate each provided schedule.
        for cid, sel_sched in selected_schedules.items():
            cust = customer_lookup.get(cid)
            if cust is None:
                raise ValueError(f"Customer id {cid} in selected_schedules not found in customer list.")
            if sel_sched not in cust["schedules"]:
                raise ValueError(
                    f"Selected schedule {sel_sched} for customer {cid} is not among candidate schedules {cust['schedules']}.")
            if len(sel_sched) != period_length:
                raise ValueError(f"Selected schedule for customer {cid} does not match period_length {period_length}.")

        # Process tours for each day.
        tours = kwargs.get("tours")
        if not isinstance(tours, dict):
            raise ValueError("Solution must include a dictionary 'tours'.")

        total_length = 0.0

        def euclidean(a, b):
            return math.sqrt((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2)

        # Evaluate each day.
        for day in range(1, period_length + 1):
            # Validate the number of tours does not exceed the available vehicles.
            tours_day = tours.get(day, [])
            vehicles_available = vehicles_per_day[day - 1]
            if len(tours_day) > vehicles_available:
                raise ValueError(
                    f"On day {day}: Number of tours ({len(tours_day)}) exceeds available vehicles ({vehicles_available}).")

            # Determine all customers that should receive service today.
            expected_customers = set()
            for cust in customers:
                if cust["id"] == 0:
                    continue
                sched = selected_schedules.get(cust["id"])
                if sched is not None and sched[day - 1] == 1:
                    expected_customers.add(cust["id"])

            visited_today = []
            for tour in tours_day:
                # A valid tour must have at least depot, one customer, and depot again.
                if len(tour) < 3:
                    raise ValueError(f"Tour {tour} on day {day} is too short.")
                # Check that the tour starts and ends with the depot.
                if tour[0] != 0 or tour[-1] != 0:
                    raise ValueError(f"Tour {tour} on day {day} must start and end at the depot (id 0).")
                # Ensure no depot visits occur in the middle.
                if 0 in tour[1:-1]:
                    raise ValueError(f"Tour {tour} on day {day} contains an extra depot visit in the middle.")

                seen_in_tour = set()
                # Process customer visits in the tour (excluding depot at the beginning and end).
                for vid in tour[1:-1]:
                    if vid in seen_in_tour:
                        raise ValueError(f"Tour on day {day} visits customer {vid} more than once.")
                    seen_in_tour.add(vid)
                    visited_today.append(vid)

                # Check the capacity constraint for the tour.
                capacity_used = sum(customer_lookup[vid]["demand"] for vid in tour[1:-1])
                if capacity_used > vehicle_capacity:
                    raise ValueError(
                        f"Tour on day {day} exceeds capacity: used {capacity_used}, capacity is {vehicle_capacity}.")

                # Compute the tour's travel distance.
                tour_length = 0.0
                prev = depot
                for vid in tour[1:]:
                    curr = depot if vid == 0 else customer_lookup.get(vid)
                    if curr is None:
                        raise ValueError(f"Customer id {vid} in tour on day {day} not found.")
                    tour_length += euclidean(prev, curr)
                    prev = curr
                total_length += tour_length

            # Ensure that the visited customers exactly match those expected for the day.
            if set(visited_today) != expected_customers:
                missing = expected_customers - set(visited_today)
                extra = set(visited_today) - expected_customers
                err_msg = f"On day {day}: "
                if missing:
                    # Only showing a sample of missing customers
                    err_msg += f"Missing visits for customers such as {list(missing)[:10]}. "
                if extra:
                    err_msg += f"Extra visits for customers {list(extra)}."
                raise ValueError(err_msg)

        return total_length

    def norm_score(self, results):
        optimal_scores = {
            "prvp1.txt": [547.9],
            "prvp2.txt": [1487.6],
            "prvp3.txt": [550.1],
            "prvp4.txt": [872.3],
            "prvp5.txt": [2207.9],
            "prvp6.txt": [965.7],
            "prvp7.txt": [839.2],
            "prvp8.txt": [2294.2],
            "prvp9.txt": [925.0],
            "prvp10.txt": [1819.2],
        }

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
        dev = {'prvp1.txt': [], 'prvp3.txt': [], 'prvp5.txt': [],
               'prvp7.txt': [], 'prvp9.txt': []}

        return dev








