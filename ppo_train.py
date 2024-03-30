from stable_baselines3 import PPO
from engine.my_env import MyPokerEnv, process_observation
from python_skeleton.ppo_bot import PPOBot


class PPOopp(PPOBot):
    def predict(self, obs):
        obs = process_observation(obs)
        act = self.model.predict(obs)[0]

        opp_contribution = 400 - obs["opp_stack"][0]
        min_raise = obs["min_raise"][0]

        raise_amount = int(act[0] * 400)
        self.log.append("Predicted raise amount: " + str(raise_amount))
        if raise_amount < opp_contribution:
            action = (2, 0)
        elif raise_amount < min_raise:
            action = (1, 0)
        else:
            action = (3, raise_amount)
        return action


env = MyPokerEnv(1, PPOopp("ppo_poker"))
model = PPO("MultiInputPolicy", env, verbose=1)

model.learn(total_timesteps=250)
model.save("ppo_poker", exclude=["env"])

del model
model = PPO.load("ppo_poker")
print(model.predict(env.reset()[0])[0])
print(model.policy)
