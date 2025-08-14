import gym
import numpy as np

# 初始化Acrobot-v1环境
env = gym.make('Acrobot-v1')  # , render_mode='human'


# 定义动作选择函数
def choose_action(ct1: float, st1: float, ct2: float, st2: float, avt1: float, avt2: float, last_action: int) -> int:
    if ct1 >= 0 and st1 >= 0 and avt1 < 0:
        action = 2
    elif st1 < 0 and avt1 == 0 and st2 < 0 and avt2 == 0:
        action = 0
    elif last_action == 2:
        action = 0
    else:
        action = 2

    return action


# 环境重置
observation, _ = env.reset()

done = False
step = 0
action = 1
while not done:
    step += 1
    theta1, theta2, theta1_dot, theta2_dot, avt1, avt2 = observation  # 提取状态信息
    action = choose_action(theta1, theta2, theta1_dot, theta2_dot, avt1, avt2, action)  # 决策动作

    # 执行动作并获得新状态
    observation, reward, done, t, info = env.step(action)

    print(f"Step: {step}")
    print(f"Theta1: {theta1}, Theta2: {theta2}")
    print(f"Theta1_dot: {theta1_dot}, Theta2_dot: {theta2_dot}")
    print(f"Action: {action}, Reward: {reward}, Done: {done}")
    print(f"{(step + 1) / 500}")

    # 渲染环境
    env.render()

# 关闭环境
env.close()
