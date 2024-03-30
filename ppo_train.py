from stable_baselines3 import PPO
from engine.my_env import MyPokerEnv

env = MyPokerEnv(1)
model = PPO("MultiInputPolicy", env, verbose=1)
env.opp_bot = model

model.learn(total_timesteps=250)
model.save("ppo_poker", exclude=["env"])

del model
model = PPO.load("ppo_poker")
print(model.predict(env.reset()[0])[0])
print(model.policy)
