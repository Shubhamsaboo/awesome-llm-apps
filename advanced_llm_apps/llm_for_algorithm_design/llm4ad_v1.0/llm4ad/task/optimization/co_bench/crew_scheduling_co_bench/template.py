template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(N: int, K: int, time_limit: float, tasks: dict, arcs: dict) -> dict:
    """
    Solves the crew scheduling problem.
    The problem consists of assigning each task (with a defined start and finish time) to exactly one crew,
    such that:
      - The tasks within each crew are executed in non-overlapping order.
      - For every consecutive pair of tasks in a crew’s schedule, a valid transition arc exists (with an associated cost).
      - The overall duty time (finish time of the last task minus start time of the first task) does not exceed the specified time limit.
      - Exactly K crews are used.
    Input kwargs (for one case):
      - N (int): Number of tasks.
      - K (int): Maximum number of crews to be used.
      - time_limit (float): Maximum allowed duty time.
      - tasks (dict): Dictionary mapping task ID (1 to N) to a tuple (start_time, finish_time).
      - arcs (dict): Dictionary mapping (from_task, to_task) pairs to transition cost.
    Evaluation metric:
      - If all constraints are met (no task overlap, valid transition arcs, duty time within the limit, and exactly K crews used), the score is the sum of transition costs across all crews.
      - If any constraint is violated, the solution is infeasible and receives no score.
      - A lower score indicates a more cost-effective solution.
    Returns:
      dict: A dictionary with one key "crews", whose value is a list of lists. Each inner list is a sequence of task IDs (integers)
            representing one crew’s schedule.
    """
    # --- placeholder implementation ---
    # For example, here we distribute tasks evenly across K crews.
    N = kwargs.get("N")
    K = kwargs.get("K")
    tasks_ids = list(range(1, N + 1))
    crews = [[] for _ in range(K)]
    for i, task in enumerate(tasks_ids):
        crews[i % K].append(task)
    # In practice, you would implement a heuristic or optimization method that groups tasks into exactly K crews
    # while satisfying the non-overlap, valid transitions, and duty time constraints.
    return {"crews": crews}
'''

task_description = ("The Crew Scheduling Problem involves assigning each task—with defined start and finish times—to "
                    "exactly one crew, aiming to minimize the total transition costs between consecutive tasks. Each "
                    "crew’s schedule must satisfy three constraints: tasks within a crew must not overlap; valid "
                    "transitions (with associated costs) must exist between every consecutive pair of tasks; and the "
                    "crew’s total duty time (from the start of the first task to the finish of the last) cannot "
                    "exceed a specified time limit. Additionally, no more than K crews can be used to cover all "
                    "tasks. Solutions violating any of these constraints are considered infeasible and receive no "
                    "score. The optimization objective is therefore to determine assignments of tasks to no more than "
                    "K crews that minimize the sum of transition costs while strictly adhering to all constraints, "
                    "yielding a feasible and cost-effective scheduling solution. "
                    "Help me design a novel algorithm to solve this problem.")
