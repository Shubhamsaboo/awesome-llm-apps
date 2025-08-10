import random
import gym
import numpy as np
import random


def choose_action(state, reward, last_action):
    x, y, x_vel, y_vel, angle, angular_vel, leg1_contact, leg2_contact = state

    if y < 0.5 and y_vel < -0.1:
        action = 2  # Fire upward engine if below target and moving downward
    elif angle > 0.1 and angular_vel > 0:
        action = 3  # Fire right orientation engine if orientation needs adjustment
    else:
        if reward < 0.5:
            if random.uniform(0, 1) < 0.7:
                action = 0  # Do nothing
            else:
                action = 1  # Fire left orientation engine
        else:
            if random.uniform(0, 1) < 0.5:
                action = 2  # Fire upward engine
            else:
                action = 3  # Fire right orientation engine
    return action


# 创建LunarLander-v2环境
env = gym.make('LunarLander-v2', render_mode='human')

# 重置环境
state, _ = env.reset()

done = False

step = 0
while not done:
    # 随机采取一个动作
    step += 1
    action = 0
    # action = env.action_space.sample()
    action = choose_action(state, 0, action)

    # 环境采取动作并返回新的状态、奖励等
    state, reward, done, t, info = env.step(action)

    print(f"step: {step}, state: {state}, reward: {reward}, done: {done}, t: {t}, action: {action}")

    # 渲染环境
    env.render()

# 关闭环境
env.close()
