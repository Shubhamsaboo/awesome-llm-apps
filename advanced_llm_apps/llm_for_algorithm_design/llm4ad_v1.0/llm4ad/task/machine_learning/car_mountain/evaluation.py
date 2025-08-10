# Module Name: CarMountainEvaluation
# Last Revision: 2025/3/5
# Description: Designs a heuristic strategy function for controlling a car along an uneven road (Mountain Car problem).
#              The function selects actions based on the car's position and velocity to efficiently guide the car
#              towards a target in the minimum number of steps.
#              This module is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Parameters:
#    -   position: float - Car's position, range [-1.2, 0.6] (default: None).
#    -   velocity: float - Car's velocity, range [-0.07, 0.07] (default: None).
#    -   last_action: int - Car's last move, values [0, 1, 2] (default: None).
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

from llm4ad.base import Evaluation
from llm4ad.task.machine_learning.car_mountain.template import template_program, task_description

__all__ = ['CarMountainEvaluation']


def evaluate(env: gym.Env, action_select: callable) -> float:
    """Evaluate heuristic function on car mountain problem."""

    observation, _ = env.reset()  # initialization
    action = 1  # initial action, stay static

    for i in range(env._max_episode_steps):
        action = action_select(observation[0], observation[1], action)
        observation, reward, done, truncated, info = env.step(action)

        if done:
            return -(i / env._max_episode_steps)  # succeed

        if truncated:
            return -(max(0.5 - observation[0], 0) + 1)  # failed


class CarMountainEvaluation(Evaluation):
    """Evaluator for car mountain problem."""

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
        self.env = gym.make('MountainCar-v0')
        self.env._max_episode_steps = max_steps

    def evaluate_program(self, program_str: str, callable_func: callable) -> Any | None:
        return evaluate(self.env, callable_func)
