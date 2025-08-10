# Module Name: OscillatorEvaluation2
# Last Revision: 2025/3/5
# Description: Provides a mathematical function skeleton for calculating acceleration in a damped nonlinear oscillator
#              system with driving force. The function takes time, position, velocity, and a set of parameters as inputs
#              and returns the resulting acceleration.
#              This module is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Parameters:
#    -   t: np.ndarray - array representing time (default: None).
#    -   x: np.ndarray - array representing observations of current position (default: None).
#    -   v: np.ndarray - array representing observations of velocity (default: None).
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
from llm4ad.task.science_discovery.oscillator2.template import template_program, task_description
from llm4ad.task.science_discovery.oscillator2 import train

__all__ = ['OscillatorEvaluation2']

MAX_NPARAMS = 10
params = [1.0] * MAX_NPARAMS


def evaluate(data: dict, equation: callable) -> float | None:
    """ Evaluate the equation on data observations."""

    # Load data observations
    inputs, outputs = data['inputs'], data['outputs']
    t, x, v = inputs[:, 0], inputs[:, 1], inputs[:, 2]

    # Optimize parameters based on data
    from scipy.optimize import minimize
    def loss(params):
        y_pred = equation(t, x, v, params)
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


class OscillatorEvaluation2(Evaluation):

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
    def equation(t: np.ndarray, x: np.ndarray, v: np.ndarray, params: np.ndarray) -> np.ndarray:
        """ Mathematical function for acceleration in a damped nonlinear oscillator

        Args:
            t: A numpy array representing time.
            x: A numpy array representing observations of current position.
            v: A numpy array representing observations of velocity.
            params: Array of numeric constants or parameters to be optimized

        Return:
            A numpy array representing acceleration as the result of applying the mathematical function to the inputs.
        """
        dv = params[0] * t + params[1] * x + params[2] * v + + params[3]
        return dv


    eval = OscillatorEvaluation2()
    res = eval.evaluate_program('', equation)
    print(res)
