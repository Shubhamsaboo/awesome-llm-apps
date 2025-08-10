# Module Name: FeynmanEvaluation
# Last Revision: 2025/3/5
# Description: Implements a mathematical function skeleton for fitting a dataset.
#              The function uses given parameters to compute outputs based on
#              input data. The goal is to optimize the parameters to best fit
#              the dataset. This module is part of the LLM4AD project
#              (https://github.com/Optima-CityU/llm4ad).
#
# Parameters:
#    -   x_s: np.ndarray - a 2-dimensional numpy array representing the input data (default: None).
#    -   params: np.ndarray - array of numeric constants or parameters to be optimized (default: None).
#    -   timeout_seconds: int - Maximum allowed time (in seconds) for the evaluation process (default: 20).
#
# References:
#   - Matsubara, Yoshitomo, et al. "Rethinking symbolic regression datasets and benchmarks
#       for scientific discovery." arXiv preprint arXiv:2206.10540 (2022).
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

import re
import itertools
from typing import Any
import numpy as np


# this line will proceed for about 10s to get all feynman equation.
from llm4ad.task.science_discovery.feynman_srsd.feynman_equations import FEYNMAN_EQUATION_CLASS_List

from llm4ad.base import Evaluation
from llm4ad.task.science_discovery.feynman_srsd.template import template_program, task_description

__all__ = ['FeynmanEvaluation']

MAX_NPARAMS = 10
params = [1.0] * MAX_NPARAMS

def evaluate(data: dict, equation: callable) -> float | None:
    """ Evaluate the equation on data observations."""

    # Load data observations
    inputs, outputs = data['inputs'], data['outputs']

    # Optimize parameters based on data
    from scipy.optimize import minimize
    def loss(params):
        y_pred = equation(inputs, params)
        return np.mean((y_pred - outputs) ** 2)

    loss_partial = lambda params: loss(params)
    result = minimize(loss_partial, [1.0]*MAX_NPARAMS, method='BFGS')

    # Return evaluation score
    optimized_params = result.x
    loss = result.fun

    if np.isnan(loss) or np.isinf(loss):
        return None
    else:
        return -loss


class FeynmanEvaluation(Evaluation):

    def __init__(self, timeout_seconds=20, test_id=1, sample_size=5000, **kwargs):
        """
        Args:
            timeout_seconds: evaluate time limit.
            test_id: test equation id ranges from [1, 120].
        """

        # read number of variables and rewrite the template
        eq_name = list(FEYNMAN_EQUATION_CLASS_List)
        self.func = FEYNMAN_EQUATION_CLASS_List[test_id-1]()
        x_len = len(self.func.x)

        template_program_temp = template_program.split('\n')
        template_program_temp[6] = template_program_temp[6].replace('.', f' with a size of {x_len}.')
        template_program_temp[7] = template_program_temp[7].replace('.', f' with a maximum size of {MAX_NPARAMS}.')

        new_template_program = '\n'.join(template_program_temp) + '\n'

        super().__init__(
            template_program=new_template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds
        )

        # sample dataset
        data_x = []
        for i in range(x_len):
            data_x.append(self.func.sampling_objs[i](sample_size))
        data_y = self.func.eq_func(data_x)

        data_x = np.array(data_x)
        data_y = np.array(data_y)
        # data_combined = np.concatenate((data_x, data_y.reshape(1, -1)), axis=0)
        # dataset = data_combined.T

        self._datasets = {
            'inputs': data_x,
            'outputs': data_y,
        }

    def evaluate_program(self, program_str: str, callable_func: callable) -> Any | None:
        return evaluate(self._datasets, callable_func)


if __name__ == '__main__':
    print(FEYNMAN_EQUATION_CLASS_List)
    print()
