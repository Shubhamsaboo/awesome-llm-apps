import numpy as np
import pandas as pd
import time
import gym
import tqdm
import csv
import os
import pickle
from queue import Queue


class QLearning:
    def __init__(self, actions_space, learning_rate=0.01, reward_decay=0.99, e_greedy=0.6):
        self.actions = actions_space  # 动作空间
        self.lr = learning_rate  # 学习率
        self.gamma = reward_decay  # 回报衰减率
        self.epsilon = e_greedy  # 探索/利用 贪婪系数
        self.num_pos = 20  # 位置分为num_pos份
        self.num_vel = 14  # 速度分为num_vel份
        self.q_table = np.random.uniform(low=-1, high=1, size=(self.num_pos * self.num_vel, self.actions.n))  # Q值表
        self.pos_bins = self.toBins(-1.2, 0.6, self.num_pos)
        self.vel_bins = self.toBins(-0.07, 0.07, self.num_vel)

    def choose_action(self, state):
        if np.random.uniform() < self.epsilon:
            action = np.argmax(self.q_table[state])
        else:
            action = self.actions.sample()
        return action

    def toBins(self, clip_min, clip_max, num):
        return np.linspace(clip_min, clip_max, num + 1)

    def digit(self, x, bin):
        n = np.digitize(x, bins=bin)
        if x == bin[-1]:
            n = n - 1
        return n

    def digitize_state(self, observation):
        cart_pos, cart_v = observation
        digitized = [self.digit(cart_pos, self.pos_bins),
                     self.digit(cart_v, self.vel_bins)]
        return (digitized[1] - 1) * self.num_pos + digitized[0] - 1

    def learn(self, state, action, r, next_state):
        next_action = np.argmax(self.q_table[next_state])
        q_predict = self.q_table[state, action]
        q_target = r + self.gamma * self.q_table[next_state, next_action]
        self.q_table[state, action] += self.lr * (q_target - q_predict)


def train():
    env = gym.make('MountainCar-v0')  # 指定渲染模式为 human
    # print(env.action_space)
    agent = QLearning(env.action_space)

    # use tqdm
    for i in tqdm.tqdm(range(10000)):  # 训练次数
        observation, _ = env.reset()  # 状态
        state = agent.digitize_state(observation)  # 状态标准化
        for t in range(300):  # 一次训练最大运行次数
            action = agent.choose_action(state)  # 动作
            observation, reward, done, truncated, info = env.step(action)
            next_state = agent.digitize_state(observation)

            if reward == 0:  # 到达山顶时 reward 为 0
                reward += 1000  # 给大一点的奖励

            # print(f"step: {t}", action, reward, done, state, next_state, truncated)
            agent.learn(state, action, reward, next_state)
            state = next_state

            # env.render()  # 每一步渲染画面

            if done or truncated:  # 重新加载环境
                # print("Episode {} finished after {} timesteps".format(i, t + 1))
                break

    print(agent.q_table)
    env.close()

    # 保存模型
    with open(os.getcwd() + '/carmountain.model', 'wb') as f:
        pickle.dump(agent, f)


def taste():
    # env = gym.make('MountainCar-v0', render_mode='human')  # 指定渲染模式为 human
    env = gym.make('MountainCar-v0')  # 指定渲染模式为 human

    print(env.action_space)
    with open(os.getcwd() + '/carmountain.model', 'rb') as f:
        agent = pickle.load(f)
    agent.actions = env.action_space  # 初始化
    agent.epsilon = 1
    observation, _ = env.reset()  # 初始化状态
    state = agent.digitize_state(observation)  # 状态标准化

    for t in range(500):  # 一次测试最大运行次数
        action = agent.choose_action(state)  #
        observation, reward, done, truncated, info = env.step(action)
        next_state = agent.digitize_state(observation)
        print(f"step: {t}", action, reward, done, state, next_state)
        # agent.learn(state, action, reward, next_state)
        state = next_state
        env.render()  # 渲染画面
    env.close()  # 关闭环境


import numpy as np


def choose_action(pos: float, v: float, last_action: int) -> int:
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
        return 0  # Accelerate left if moving backwards and past target
    elif v > 0 and pos < target_pos:
        return 2  # Accelerate right if moving forwards and before target
    elif abs(distance_to_target) < 0.1:  # If close to target, stabilize
        return 1  # Don't accelerate, maintain current state
    elif distance_to_target > 0:
        return 2  # Move right towards the target
    else:
        return 0  # Move left away from the target


def run_test():
    env = gym.make('MountainCar-v0', render_mode='human')
    observation, _ = env.reset()  # 状态包括以下因素
    action = 1

    for t in range(500):
        # action = np.random.choice([0, 1, 2])  # 动作
        action = choose_action(observation[0], observation[1], action)
        observation, reward, done, truncated, info = env.step(action)
        print(f"step: {t}")
        # print(action, reward, done)
        # print(observation)
        env.render()
        # time.sleep(0.02)

        if done:
            break

    env.close()


if __name__ == '__main__':
    # train()  # 训练
    run_test()  # 训练结束后测试
