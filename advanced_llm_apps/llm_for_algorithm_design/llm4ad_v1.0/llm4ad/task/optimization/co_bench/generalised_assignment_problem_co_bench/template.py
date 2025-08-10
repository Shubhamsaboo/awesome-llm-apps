template_program = '''
import numpy as np
import scipy.optimize as opt
def solve(m:int, n:int, cost_matrix:list, consumption_matrix:list, capacities:list, problem_type:str='max') -> dict:
    """
    Solve the Generalised Assignment Problem (GAP) for a single case.
    Input arguments (passed as keyword arguments):
      - m: (int) Number of agents.
      - n: (int) Number of jobs.
      - cost_matrix: (list of list of float) A matrix of size m×n where cost_matrix[i][j]
                     represents the cost of assigning job j to agent i.
      - consumption_matrix: (list of list of float) A matrix of size m×n where consumption_matrix[i][j]
                     represents the resource consumed when job j is assigned to agent i.
      - capacities: (list of float) A list of length m containing the resource capacity for each agent.
      - problem_type: (str, optional) Indicates whether the problem is a 'max' or 'min' problem.
                     Defaults to 'max'.
    Returns:
      A dictionary with the key 'assignments' whose value is a list of n integers.
      Each integer is an agent number (using 1-indexing) that is assigned to the corresponding job.
    """
    # For illustration purposes, we provide a trivial solution that assigns every job to agent 1.
    assignments = [1] * kwargs['n']
    return {'assignments': assignments}
'''

task_description = ("The Generalized Assignment Problem (GAP) involves assigning \( n \) jobs to \( m \) agents such "
                    "that each job is assigned to exactly one agent, and the resource consumption for each agent does "
                    "not exceed its capacity. The objective is to optimize the total cost based on the problem type. "
                    "When formulated as a maximization problem, the goal is to maximize the total cost; when "
                    "formulated as a minimization problem, the goal is to minimize the total cost. Given a cost "
                    "matrix (representing the cost of assigning jobs to agents), a consumption matrix (indicating the "
                    "resource usage per assignment), and capacities (the resource limits for each agent), the task is "
                    "to find a valid assignment that meets the capacity constraints while optimizing the total cost "
                    "as specified by the problem indicator."
                    "Help me design a novel algorithm to solve this problem.")
