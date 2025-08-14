# Module Name: SSEvaluation
# Last Revision: 2025/3/5
# Description: Provides a mathematical function skeleton for calculating stress in an Aluminium rod.
#              The function is designed to work for both elastic and plastic regions, taking strain,
#              temperature, and a set of parameters as inputs, and returning the resulting stress.
#              This module is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Parameters:
#    -   strain: np.ndarray - array representing observations of strain (default: None).
#    -   temp: np.ndarray - array representing observations of temperature (default: None).
#    -   params: np.ndarray - array of numeric constants or parameters to be optimized (default: None).
#    -   timeout_seconds: int - Maximum allowed time (in seconds) for the evaluation process (default: 20).
#
# References:
#   - Shojaee, Parshin, et al. "Llm-sr: Scientific equation discovery via programming
#       with large language models." arXiv preprint arXiv:2404.18400 (2024).
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
import pandas as pd
import numpy as np

from llm4ad.base import Evaluation
from llm4ad.task.science_discovery.stresstrain.template import template_program, task_description
from llm4ad.task.science_discovery.stresstrain import train

__all__ = ['SSEvaluation']

MAX_NPARAMS = 10
params = [1.0] * MAX_NPARAMS


def evaluate(data: dict, equation: callable) -> float | None:
    """ Evaluate the equation on data observations."""

    # Load data observations
    inputs, outputs = data['inputs'], data['outputs']
    strain, temp = inputs[:, 0], inputs[:, 1]

    # Optimize parameters based on data
    from scipy.optimize import minimize
    def loss(params):
        y_pred = equation(strain, temp, params)
        return np.mean((y_pred - outputs) ** 2)

    loss_partial = lambda params: loss(params)
    result = minimize(loss_partial, [1.0] * MAX_NPARAMS, method='BFGS')

    # Return evaluation score
    optimized_params = result.x
    loss = result.fun

    if np.isnan(loss) or np.isinf(loss):
        return None
    else:
        return -loss


class SSEvaluation(Evaluation):

    def __init__(self, timeout_seconds=20, **kwargs):
        super().__init__(
            template_program=template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds
        )

        # read csv
        # df = pd.read_csv(os.path.join(os.path.dirname(__file__), './_data/train.csv'))
        df = pd.DataFrame(train.data)
        data = np.array(df)
        X = data[:, :-1]
        y = data[:, -1].reshape(-1)
        self._datasets = {'inputs': X, 'outputs': y}

    def evaluate_program(self, program_str: str, callable_func: callable) -> Any | None:
        return evaluate(self._datasets, callable_func)


if __name__ == '__main__':
    def equation(strain: np.ndarray, temp: np.ndarray, params: np.ndarray) -> np.ndarray:
        """ Mathematical function for stress in Aluminium rod

        Args:
            strain: A numpy array representing observations of strain.
            temp: A numpy array representing observations of temperature.
            params: Array of numeric constants or parameters to be optimized

        Return:
            A numpy array representing stress as the result of applying the mathematical function to the inputs.
        """
        return params[0] * strain + params[1] * temp


    eval = SSEvaluation()
    res = eval.evaluate_program('', equation)
    print(res)
