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
from llm4ad.task.optimization.co_bench.aircraft_landing_co_bench.template import template_program, task_description

__all__ = ['ALEvaluationCB']


class ALEvaluationCB(Evaluation):
    """Evaluator for aircraft landing."""

    def __init__(self,
                 timeout_seconds=60,
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
        dataset = load_subdir_as_text("CO-Bench/CO-Bench", "Aircraft landing")
        self._datasets = {}
        for i in range(1, 14):  # airland1 to airland13
            filename = f"airland{i}.txt"
            if filename in dataset:
                # Join all text rows into a single string
                text_content = '\n'.join([row['text'] for row in dataset[filename]])
                self._datasets[filename] = text_content

    def evaluate_program(self, program_str: str, callable_func: callable, **kwargs) -> Any | None:
        return self.evaluate(callable_func)

    def evaluate(self, eva: callable) -> float | None:
        ins_cases = []
        
        # Define runway configurations for each dataset (corresponds to airland1-13)
        runway_configs = [[1, 2, 3],
                         [1, 2, 3],
                         [1, 2, 3],
                         [1, 2, 3, 4],
                         [1, 2, 3, 4],
                         [1, 2, 3],
                         [1, 2],
                         [1, 2, 3],
                         [1, 2, 3, 4],
                         [1, 2, 3, 4, 5],
                         [1, 2, 3, 4, 5],
                         [1, 2, 3, 4, 5],
                         [1, 2, 3, 4, 5]]
        
        for case_id, ins in enumerate(self._datasets.values()):
            base_case = self.load_data(ins)
            # Create variations with different runway configurations
            for num_runways in runway_configs[case_id]:
                case_with_runways = base_case.copy()
                case_with_runways['num_runways'] = num_runways
                ins_cases.append(case_with_runways)

        penalties = []
        try:
            for case in ins_cases:
                schedule = eva(case['num_planes'], case['num_runways'], case['freeze_time'], case['planes'], case['separation'])
                penalty = self.eval_func(num_planes=case['num_planes'], num_runways=case['num_runways'],
                                         freeze_time=case['freeze_time'], separation=case['separation'], planes=case['planes'],
                                         schedule=schedule['schedule'])
                penalties.append(penalty)

            return -np.mean(penalties)

        except ValueError as e:
            print(e)
            return None

    def load_data(self, input_str):
        """
        Reads the aircraft landing scheduling problem instance from a string.
        The string contains a single case with the following format:
            Line 1: <num_planes> <freeze_time>
            For each plane (i = 1, …, num_planes):
                - A line with 6 numbers:
                      appearance_time earliest_landing_time target_landing_time
                      latest_landing_time penalty_cost_early penalty_cost_late
                - One or more subsequent lines containing exactly num_planes separation times.
                  (Separation times for plane i with respect to planes 1..num_planes. They may span multiple lines.)
        Returns:
            A dictionary containing the keys:
                - "num_planes"  : int
                - "freeze_time" : float
                - "planes"      : list of dicts (one per plane)
                - "separation"  : list of lists of floats
        """
        all_lines = input_str.split("\n")
        all_lines = [line.strip() for line in all_lines if line.strip()]

        idx = 0
        total_lines = len(all_lines)
        
        # Parse the first line: num_planes and freeze_time.
        try:
            tokens = all_lines[idx].split()
            num_planes = int(tokens[0])
            freeze_time = float(tokens[1])
        except Exception as e:
            raise ValueError(f"Error parsing case header at line {idx + 1}: {e}")
        idx += 1

        planes = []
        separation = []

        for plane_index in range(num_planes):
            if idx >= total_lines:
                raise ValueError(f"Insufficient lines for plane {plane_index + 1} parameters.")
            params_tokens = all_lines[idx].split()
            idx += 1
            if len(params_tokens) < 6:
                raise ValueError(f"Plane {plane_index + 1}: Expected 6 parameters, got {len(params_tokens)}.")
            try:
                appearance = float(params_tokens[0])
                earliest = float(params_tokens[1])
                target = float(params_tokens[2])
                latest = float(params_tokens[3])
                penalty_early = float(params_tokens[4])
                penalty_late = float(params_tokens[5])
            except Exception as e:
                raise ValueError(f"Plane {plane_index + 1}: Error converting parameters: {e}")

            planes.append({
                "appearance": appearance,
                "earliest": earliest,
                "target": target,
                "latest": latest,
                "penalty_early": penalty_early,
                "penalty_late": penalty_late
            })

            # Read exactly num_planes separation times (may span multiple lines)
            sep_tokens = []
            while len(sep_tokens) < num_planes:
                if idx >= total_lines:
                    raise ValueError(f"Not enough lines to read separation times for plane {plane_index + 1}.")
                sep_tokens.extend(all_lines[idx].split())
                idx += 1
            # In case more tokens were read than needed:
            sep_tokens = sep_tokens[:num_planes]
            try:
                sep_times = [float(token) for token in sep_tokens]
            except Exception as e:
                raise ValueError(f"Plane {plane_index + 1}: Error converting separation times: {e}")
            separation.append(sep_times)

        # Return a single case dictionary (without num_runways, as that will be added later)
        return {
            "num_planes": num_planes,
            "freeze_time": freeze_time,
            "planes": planes,
            "separation": separation,
        }

    def eval_func(self, **kwargs):
        """
        Evaluates a proposed aircraft landing schedule.
        Expects the following keys in kwargs:
            - num_planes  : int, number of planes.
            - num_runways : int, number of runways.
            - freeze_time : float.
            - planes      : list of dicts, each containing:
                              "earliest", "target", "latest", "penalty_early", "penalty_late".
            - separation  : list of lists (floats), where separation[i][j] is the required gap after plane i lands
                            before plane j can land when they are assigned to the same runway.
            - schedule    : dict mapping plane_id (1-indexed) to a dict with keys:
                              "landing_time" (float) and "runway" (int).
        The evaluation performs these checks:
            1. Each plane's landing time is within its allowed time window.
            2. Each plane is assigned to a runway in the range [1, num_runways].
            3. For every two distinct planes i and j assigned to the same runway,
               if plane i lands at or before plane j then the gap must be at least
               the required separation time.
        The total penalty is computed as follows for each plane:
            - If landing_time < target: penalty = (target - landing_time) * penalty_early.
            - If landing_time > target: penalty = (landing_time - target) * penalty_late.
            - If landing_time == target: no penalty.
        Returns:
            The total penalty (a float) if the schedule is feasible.
        Raises:
            ValueError with an informative message if any constraint is violated.
        """
        # Extract required parameters.
        num_planes = kwargs.get("num_planes")
        num_runways = kwargs.get("num_runways")
        planes = kwargs.get("planes")
        separation = kwargs.get("separation")
        schedule = kwargs.get("schedule")

        # Check that schedule has exactly num_planes entries.
        if not isinstance(schedule, dict) or len(schedule) != num_planes:
            raise ValueError(f"Schedule must be a dict with exactly {num_planes} entries.")

        for plane_id in range(1, num_planes + 1):
            if plane_id not in schedule:
                raise ValueError(f"Plane {plane_id} is missing in the schedule.")
            # Each schedule entry must be a dict with 'landing_time' and 'runway'
            entry = schedule[plane_id]
            if not isinstance(entry, dict) or "landing_time" not in entry or "runway" not in entry:
                raise ValueError(f"Schedule entry for plane {plane_id} must contain 'landing_time' and 'runway' keys.")
            # Check runway assignment is valid.
            runway = entry["runway"]
            if not isinstance(runway, int) or runway < 1 or runway > num_runways:
                raise ValueError(
                    f"Plane {plane_id} assigned runway {runway} is invalid. Must be between 1 and {num_runways}.")

        # 1. Check landing time window constraints.
        for i in range(1, num_planes + 1):
            landing_time = schedule[i]["landing_time"]
            earliest = planes[i - 1]["earliest"]
            latest = planes[i - 1]["latest"]
            if landing_time < earliest or landing_time > latest:
                raise ValueError(
                    f"Plane {i}: Landing time {landing_time} is outside the allowed window [{earliest}, {latest}]."
                )

        # 2. Check separation constraints for planes on the same runway.
        for i in range(1, num_planes + 1):
            for j in range(1, num_planes + 1):
                if i == j:
                    continue
                entry_i = schedule[i]
                entry_j = schedule[j]
                # Only check separation if both planes are assigned to the same runway.
                if entry_i["runway"] == entry_j["runway"]:
                    L_i = entry_i["landing_time"]
                    L_j = entry_j["landing_time"]
                    # If plane i lands no later than plane j, check the required separation.
                    if L_i <= L_j:
                        required_gap = separation[i - 1][j - 1]
                        if (L_j - L_i) < required_gap:
                            raise ValueError(
                                f"Separation violation on runway {entry_i['runway']}: Plane {i} lands at {L_i} and Plane {j} at {L_j} "
                                f"(required gap: {required_gap})."
                            )

        # 3. Compute total penalty.
        total_penalty = 0.0
        for i in range(1, num_planes + 1):
            landing_time = schedule[i]["landing_time"]
            target = planes[i - 1]["target"]
            if landing_time < target:
                penalty = (target - landing_time) * planes[i - 1]["penalty_early"]
            elif landing_time > target:
                penalty = (landing_time - target) * planes[i - 1]["penalty_late"]
            else:
                penalty = 0.0
            total_penalty += penalty

        return total_penalty

    def norm_score(self, results):
        optimal_scores = {
            "airland1.txt": [700, 90, 0],
            "airland2.txt": [1480, 210, 0],
            "airland3.txt": [820, 60, 0],
            "airland4.txt": [2520, 640, 130, 0],
            "airland5.txt": [3100, 650, 170, 0],
            "airland6.txt": [24442, 554, 0],
            "airland7.txt": [1550, 0],
            "airland8.txt": [1950, 135, 0],
            "airland9.txt": [7848.42, 573.25, 88.72, 0.0],
            "airland10.txt": [17726.06, 1372.21, 246.15, 34.22, 0.0],
            "airland11.txt": [19327.45, 1683.75, 333.53, 69.66, 0.0],
            "airland12.txt": [2549.24, 2204.96, 430.5, 2.86, 0.0],
            "airland13.txt": [58392.69, 4897.92, 821.82, 123.3, 0.0],
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
                    if optimal_list[idx] == 0:
                        normed_scores.append((optimal_list[idx] + 1) / (score + 1))
                    else:
                        normed_scores.append(optimal_list[idx] / score)
                else:
                    normed_scores.append(score)
            normed[case] = (normed_scores, error_message)

        return normed

    def get_dev(self):
        dev = {'airland1.txt': [0], 'airland10.txt': [2, 1], 'airland11.txt': [0, 1], 'airland12.txt': [3, 4],
               'airland13.txt': [0, 3], 'airland2.txt': [2], 'airland3.txt': [2], 'airland4.txt': [1, 3],
               'airland5.txt': [0, 1],
               'airland6.txt': [1], 'airland7.txt': [1], 'airland8.txt': [2], 'airland9.txt': [0, 1]}
        return dev

if __name__ == "__main__":
    evaluator = ALEvaluationCB()
    import random

    def solve(num_planes: int, num_runways: int, freeze_time: float, planes: list[dict],
              separation: list[list[int]]) -> dict:
        """
        Problem:
            Given an instance of the Aircraft Landing Scheduling Problem, schedule the landing time for each plane and assign a runway so that:
              - Each landing time is within its allowed time window.
              - Each plane is assigned to one runway (from the available runways).
              - For any two planes assigned to the same runway, if plane i lands at or before plane j, then the landing times must be separated by at least
                the specified separation time (provided in the input data).
              - The overall penalty is minimized. For each plane, if its landing time is earlier than its target time, a penalty
                is incurred proportional to the earliness; if later than its target time, a penalty proportional to the lateness is incurred.
              - If any constraint is violated, the solution receives no score.
        Input kwargs:
            num_planes  : (int) Number of planes.
            num_runways : (int) Number of runways.
            freeze_time : (float) Freeze time (unused in scheduling decisions).
            planes      : (list of dict) Each dictionary contains:
                            - "appearance"    : float, time the plane appears.
                            - "earliest"      : float, earliest landing time.
                            - "target"        : float, target landing time.
                            - "latest"        : float, latest landing time.
                            - "penalty_early" : float, penalty per unit time landing early.
                            - "penalty_late"  : float, penalty per unit time landing late.
            separation  : (list of lists) separation[i][j] is the required gap after plane i lands before plane j can land
                          when they are assigned to the same runway.
        Returns:
            A dictionary named "schedule" mapping each plane id (1-indexed) to a dictionary with its scheduled landing time
            and assigned runway, e.g., { plane_id: {"landing_time": float, "runway": int}, ... }.
        """
        # -----------------------
        # For demonstration purposes, we simply schedule each plane at its target time
        # and assign all planes to runway 1.
        # (Note: This solution may be infeasible if targets do not satisfy separation constraints.)
        schedule = {}
        for i, plane in enumerate(planes, start=1):
            schedule[i] = {"landing_time": plane["target"], "runway": random.randint(1, num_runways + 1)}
        return {"schedule": schedule}

    results = evaluator.evaluate_program('', solve)
    print(results)
