# Module Name: AcrobotEvaluation
# Last Revision: 2025/3/5
# Description: Designs a heuristic strategy function for controlling an acrobot system.
#              The function selects actions based on joint angles and angular velocities
#              to efficiently swing the lower link and generate momentum for the upper
#              link to reach the target height.
#              This module is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
#
# Parameters:
#    -   cos_theta1: float - cosine of theta1, range [-1, 1] (default: None).
#    -   sin_theta1: float - sine of theta1, range [-1, 1] (default: None).
#    -   cos_theta2: float - cosine of theta2, range [-1, 1] (default: None).
#    -   sin_theta2: float - sine of theta2, range [-1, 1] (default: None).
#    -   a_v_theta1: float - angular velocity of theta1, range [-12.567, 12.567] (default: None).
#    -   a_v_theta2: float - angular velocity of theta2, range [-28.274, 28.274] (default: None).
#    -   last_action: int - last action taken, values [0, 1, 2] (default: None).
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
from llm4ad.task.machine_learning.acrobot.template import template_program, task_description

__all__ = ['AcrobotEvaluation']


def evaluate(env: gym.Env, action_select: callable) -> float:
    """Evaluate heuristic function on car mountain problem."""

    observation, _ = env.reset()  # initialization
    action = 0  # initial action

    for i in range(env._max_episode_steps + 1):  # protect upper limits
        action = action_select(observation[0],
                               observation[1],
                               observation[2],
                               observation[3],
                               observation[4],
                               observation[5],
                               action)
        observation, reward, done, truncated, info = env.step(action)

        if done or truncated:
            # self.env.close()
            fitness = observation[0] + (observation[0] * observation[2] - observation[1] * observation[3]) + 2
            if fitness <= 1:
                return -(i + 1) / env._max_episode_steps
            else:
                return -fitness


class AcrobotEvaluation(Evaluation):
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
        self.env = gym.make('Acrobot-v1')
        self.env._max_episode_steps = max_steps

    def evaluate_program(self, program_str: str, callable_func: callable) -> Any | None:
        return evaluate(self.env, callable_func)
