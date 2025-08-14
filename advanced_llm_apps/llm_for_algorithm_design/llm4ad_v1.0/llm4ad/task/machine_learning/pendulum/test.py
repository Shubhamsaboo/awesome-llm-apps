import gym
import numpy as np

# 初始化Pendulum-v1环境
env = gym.make('Pendulum-v1')  # 可选：设置 render_mode='human' 以显示图形界面


# 定义动作选择函数
def choose_action(x: float, y: float, angular_velocity: float, last_action: float) -> float:
    if angular_velocity > 0 and y > 0:
        action = -2.0  # 施加一个负力矩
    elif angular_velocity < 0 and y < 0:
        action = 2.0  # 施加一个正力矩
    else:
        action = 0.0  # 保持静止力矩

    # 确保动作在 [-2.0, 2.0] 范围内
    action = np.clip(action, -2.0, 2.0)
    return action


# 环境重置
observation, _ = env.reset()

done = False
step = 0
action = 0.0  # 初始动作
env._max_episode_steps = 500

while not done and step < 500:
    step += 1
    x, y, angular_velocity = observation  # 提取状态信息 (cos(theta), sin(theta), angular_velocity)
    action = choose_action(x, y, angular_velocity, action)  # 决策动作

    # 执行动作并获得新状态
    observation, reward, done, truncated, info = env.step([action])  # 动作需要作为列表传递

    print(f"Step: {step}")
    print(f"x (cos(theta)): {x}, y (sin(theta)): {y}, Angular Velocity: {angular_velocity}")
    print(f"Action: {action}, Reward: {reward}, Done: {done}, Truncated: {truncated}")
    print(f"Progress: {(step + 1) / env._max_episode_steps:.2%}")

    # 渲染环境（可选）
    env.render()

# 关闭环境
env.close()
