# Module Name: PendulumEvaluation
# Last Revision: 2025/3/5
# Description: Implements a control strategy for the inverted pendulum swing-up problem. The function
#              selects an appropriate torque based on the pendulum's current state to swing it into an
#              upright position and stabilize it. The goal is to minimize the time required to reach
#              the upright position while ensuring stability. This module is part of the LLM4AD project
#              (https://github.com/Optima-CityU/llm4ad).
#
# Parameters:
#    -   x_position: float - cos(theta), range [-1, 1] (default: None).
#    -   y_position: float - sin(theta), range [-1, 1] (default: None).
#    -   angular_velocity: float - angular velocity of the pendulum, range [-8.0, 8.0] (default: None).
#    -   last_action: float - last torque applied to the pendulum, range [-2.0, 2.0] (default: None).
#    -   timeout_seconds: int - Maximum allowed time (in seconds) for the evaluation process (default: 20).
#
# References:
#   - Brockman, Greg, et al. "Openai gym." arXiv preprint arXiv:1606.01540 (2016).
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
import gym
import numpy as np

from llm4ad.base import Evaluation
from llm4ad.task.machine_learning.pendulum.template import template_program, task_description

__all__ = ['PendulumEvaluation']

def evaluate(env: gym.Env, action_select: callable) -> float | None:
    try:
        fitness = []
        # Parallel evaluation 4 times, core=4
        # fitness = Parallel(n_jobs=4)(delayed(evaluate_single)(env, action_select) for _ in range(5))
        for i in range(5):
            fitness.append(evaluate_single(env, action_select))
        fitness = np.mean(fitness)

        return fitness
    except Exception as e:
        return None


def evaluate_single(env: gym.Env, action_select: callable) -> float:
    """Evaluate heuristic function on the pendulum swing-up problem."""

    observation, _ = env.reset()  # initialization
    action = 0.0  # initial action (torque)
    total_reward = 0

    for i in range(env._max_episode_steps + 1):  # protect upper limits
        action = action_select(observation[0],  # cos(theta)
                               observation[1],  # sin(theta)
                               observation[2],  # angular velocity
                               action)  # last action (torque)
        observation, reward, done, truncated, info = env.step([action])
        total_reward += reward

        if done or truncated:
            # self.env.close()
            cos_theta = observation[0]
            sin_theta = observation[1]
            angular_velocity = observation[2]

            # Calculate error terms
            angle_error = abs(1 - cos_theta)  # Distance from vertical (cos(theta) = 1 when upright)
            stability_error = abs(sin_theta)  # Penalize instability

            # Total error
            error = angle_error + stability_error

            # Fitness calculation: ensure fitness > 1 and closer to 1 for better states
            fitness = 1 + error
            if fitness <= 1:
                return -(i + 1) / env._max_episode_steps
            else:
                return -fitness


class PendulumEvaluation(Evaluation):
    """Evaluator for the pendulum swing-up problem."""

    def __init__(self, max_steps=500, timeout_seconds=20, **kwargs):
        """
            Args:
                - 'max_steps' (int): Maximum number of steps allowed per episode in the Pendulum-v1 environment (default is 200).
                - '**kwargs' (dict): Additional keyword arguments passed to the parent class initializer.

            Attributes:
                - 'env' (gym.Env): The Pendulum-v1 environment with a modified maximum episode length.
        """

        super().__init__(
            template_program=template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds
        )

        self.env = None
        self.env = gym.make('Pendulum-v1')
        self.env._max_episode_steps = max_steps

    def evaluate_program(self, program_str: str, callable_func: callable) -> Any | None:
        return evaluate(self.env, callable_func)
