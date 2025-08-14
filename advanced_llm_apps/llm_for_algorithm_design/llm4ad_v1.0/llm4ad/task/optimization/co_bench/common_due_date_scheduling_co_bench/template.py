template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(jobs: List[Tuple[int, int, int]], h: float = 0.6) -> Dict[str, List[int]]:
    """
    Solves the restricted single‐machine common due date scheduling problem.
    The problem:
       Given a list of jobs where each job is represented as a tuple (p, a, b):
         • p: processing time
         • a: earliness penalty coefficient
         • b: tardiness penalty coefficient
       and an optional parameter h (default 0.6), the common due date is computed as:
             d = floor(sum(p) * h)
       A schedule (i.e., a permutation of job indices in 1‐based numbering) is produced.
       When processing the jobs in that order, the penalty is computed by:
         • Adding a × (d − C) if a job’s completion time C is less than d,
         • Adding b × (C − d) if C is greater than d,
         • No penalty if C equals d.
       The objective is to minimize the total penalty.
    Input kwargs:
         - 'jobs' (List[Tuple[int, int, int]]): a list of tuples where each tuple represents a job with:
              • p (int): processing time,
              • a (int): earliness penalty coefficient,
              • b (int): tardiness penalty coefficient.
         - Optional: 'h' (float): the factor used to compute the common due date (default is 0.6).
    Evaluation Metric:
         The computed schedule is evaluated by accumulating processing times and applying
         the appropriate earliness/tardiness penalties with respect to the common due date.
    Returns:
         A dictionary with key 'schedule' whose value is a list of integers representing
         a valid permutation of job indices (1-based).
    """
    # Placeholder implementation: simply return the jobs in their original order.
    jobs = kwargs.get('jobs', [])
    n = len(jobs)
    return {'schedule': list(range(1, n + 1))}
'''

task_description = ("The **Restricted Single-Machine Common Due Date Scheduling Problem** involves scheduling a set "
                    "of jobs on a single machine to minimize a total penalty. Each job is defined by a tuple \((p, a, "
                    "b)\), where \( p \) represents the processing time, \( a \) is the earliness penalty "
                    "coefficient, and \( b \) is the tardiness penalty coefficient. A common due date \( d \) is "
                    "determined as \( d = \lfloor \sum p \\times h \\rfloor \), where \( h \) is a predefined fraction "
                    "(defaulting to 0.6). The goal is to determine an optimal job sequence that minimizes the "
                    "penalty, calculated as follows: for each job, if its completion time \( C \) is earlier than \( "
                    "d \), an earliness penalty of \( a \\times (d - C) \) is incurred; if \( C \) exceeds \( d \), "
                    "a tardiness penalty of \( b \\times (C - d) \) is applied; otherwise, no penalty is incurred. The "
                    "problem requires finding a permutation of job indices (1-based) that minimizes the total "
                    "penalty. The evaluation metric sums these penalties for a given schedule."
                    "Help me design a novel algorithm to solve this problem.")
