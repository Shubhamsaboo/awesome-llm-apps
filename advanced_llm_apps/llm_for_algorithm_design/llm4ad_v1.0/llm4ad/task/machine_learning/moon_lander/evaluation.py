# Module Name: MoonLanderEvaluation
# Last Revision: 2025/3/5
# Description: Implements a heuristic strategy function to guide a lunar lander to achieve safe landings
#              at the center of the target area. The function selects actions based on the lander's
#              current state, aiming to minimize the number of steps required for a safe landing.
#              A "safe landing" is defined as a touchdown with minimal vertical velocity, upright
#              orientation, and angular velocity and angle close to zero.
#              This module is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Parameters:
#    -   x_coordinate: float - x coordinate, range [-1, 1] (default: None).
#    -   y_coordinate: float - y coordinate, range [-1, 1] (default: None).
#    -   x_velocity: float - x velocity (default: None).
#    -   x_velocity: float - y velocity (default: None).
#    -   angle: float - angle (default: None).
#    -   angular_velocity: float - angular velocity (default: None).
#    -   l_contact: int - 1 if the first leg has contact, else 0 (default: None).
#    -   r_contact: int - 1 if the second leg has contact, else 0 (default: None).
#    -   last_action: int - last action taken by the lander, values [0, 1, 2, 3] (default: None).
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
from llm4ad.task.machine_learning.moon_lander.template import template_program, task_description

__all__ = ['MoonLanderEvaluation']


def evaluate(env: gym.Env, action_select: callable) -> float | None:
    try:
        fitness = []
        # parallel evaluation 4 times, core=4
        # fitness = Parallel(n_jobs=4)(delayed(evaluate_single)(env, action_select) for _ in range(5))
        for i in range(5):
            fitness.append(evaluate_single(env, action_select))
        fitness = np.mean(fitness)

        return fitness
    except Exception as e:
        return None


def evaluate_single(env: gym.Env, action_select: callable) -> float:
    """Evaluate heuristic function on moon lander problem."""

    observation, _ = env.reset()  # initialization
    action = 0  # initial action
    reward = 0
    yv = []

    for i in range(env._max_episode_steps + 1):  # protect upper limits
        action = action_select(observation[0], observation[1],
                               observation[2],
                               observation[3],
                               observation[4],
                               observation[5],
                               observation[6],
                               observation[7],
                               action)
        observation, reward, done, truncated, info = env.step(action)
        yv.append(observation[3])

        if done or truncated:
            # self.env.close()
            fitness = abs(observation[0]) + abs(yv[-2]) - ((observation[6] + observation[7]) - 2) + 1
            if reward >= 100:
                return -(i + 1) / env._max_episode_steps
            else:
                return -fitness


class MoonLanderEvaluation(Evaluation):
    """Evaluator for moon lander problem."""

    def __init__(self, max_steps=500, timeout_seconds=20, **kwargs):
        """
            Args:
                - 'max_steps' (int): Maximum number of steps allowed per episode in the MountainCar-v0 environment (default is 500).
                - '**kwargs' (dict): Additional keyword arguments passed to the parent class initializer.

            Attributes:
                - 'env' (gym.Env): The MountainCar-v0 environment with a modified maximum episode length.
        """

        super().__init__(
            template_program=template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds
        )

        self.env = None
        self.env = gym.make('LunarLander-v2')
        self.env._max_episode_steps = max_steps

    def evaluate_program(self, program_str: str, callable_func: callable) -> Any | None:
        return evaluate(self.env, callable_func)
