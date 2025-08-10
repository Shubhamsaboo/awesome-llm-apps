import numpy as np
import pandas as pd
import time
import gym
import tqdm
import csv
import os
import pickle
from queue import Queue

def choose_action(pos: float, v: float, last_action: float) -> [float]:
    """Return the action for the car to proceed the next move.
    Args:
        pos: Car's position, a float ranges between [-1.2, 0.6].
        v: Car's velocity, a float ranges between [-0.07, 0.07].
        last_action: Car's next move, a int ranges between [0, 1, 2].
    Return:
         An integer representing the selected action for the car.
         0: accelerate to left
         1: don't accelerate
         2: accelerate to right
    """
    target_pos = 0.6

    # Calculate distance to target
    distance_to_target = target_pos - pos

    # Define thresholds for decision making
    if v < 0 and pos > target_pos:
        return [1]  # Accelerate left if moving backwards and past target
    elif v > 0 and pos < target_pos:
        return [1]  # Accelerate right if moving forwards and before target
    elif abs(distance_to_target) < 0.1:  # If close to target, stabilize
        return [1]  # Don't accelerate, maintain current state
    elif distance_to_target > 0:
        return [1]  # Move right towards the target
    else:
        return [0.5]  # Move left away from the target


def run_test():
    env = gym.make('MountainCarContinuous-v0', render_mode='human')
    observation, _ = env.reset()  # 状态包括以下因素
    action = 1

    for t in range(500):
        # action = np.random.choice([0, 1, 2])  # 动作
        action = choose_action(observation[0], observation[1], action)
        action = np.random.random()
        observation, reward, done, truncated, info = env.step([action])
        print(f"step: {t}, action: {action}, reward: {reward}, done: {done}, truncated: {truncated}, info: {info}")
        # print(action, reward, done)
        # print(observation)
        env.render()
        # time.sleep(0.02)

        if done:
            break

    env.close()


if __name__ == '__main__':
    run_test()  # 训练结束后测试
