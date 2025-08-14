template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(num_planes: int, num_runways: int, freeze_time: float, planes: list[dict], separation: list[list[int]]) -> dict:
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
        schedule[i] = {"landing_time": plane["target"], "runway": 1}
    return {"schedule": schedule}
'''

task_description = ("The problem is to schedule landing times for a set of planes across one or more runways such that "
                    "each landing occurs within its prescribed time window and all pairwise separation requirements "
                    "are satisfied; specifically, if plane i lands at or before plane j on the same runway, "
                    "then the gap between their landing times must be at least the specified separation time provided "
                    "in the input. In a multiple-runway setting, each plane must also be assigned to one runway, "
                    "and if planes land on different runways, the separation requirement (which may differ) is "
                    "applied accordingly. Each plane has an earliest, target, and latest landing time, with penalties "
                    "incurred proportionally for landing before (earliness) or after (lateness) its target time. The "
                    "objective is to minimize the total penalty cost while ensuring that no constraints are "
                    "violated—if any constraint is breached, the solution receives no score."
                    "Help me design a novel algorithm to solve this problem.")
