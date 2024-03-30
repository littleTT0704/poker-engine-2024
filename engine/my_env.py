from gymnasium import spaces
from .config import STARTING_STACK
from .gym_env import PokerEnv
from .roundstate import RoundState
from .actions import (
    CheckAction,
    FoldAction,
    RaiseAction,
)
import pickle
import numpy as np


class MyPokerEnv(PokerEnv):
    def __init__(self, num_rounds):
        super().__init__(num_rounds, "")

        self.action_space = spaces.Box(low=0, high=1, shape=(1,))
        cards_space = spaces.MultiDiscrete([3 * 9 + 1, 3 * 9 + 1])
        self.observation_space = spaces.Dict(
            {
                "street": spaces.Discrete(3),
                "my_cards": cards_space,
                "board_cards": cards_space,
                "my_pip": spaces.Box(low=0, high=1, shape=(1,)),
                "opp_pip": spaces.Box(low=0, high=1, shape=(1,)),
                "my_stack": spaces.Box(low=0, high=1, shape=(1,)),
                "opp_stack": spaces.Box(low=0, high=1, shape=(1,)),
                "min_raise": spaces.Box(low=0, high=1, shape=(1,)),
                "max_raise": spaces.Box(low=0, high=1, shape=(1,)),
                "equity": spaces.Box(low=0, high=1, shape=(1,)),
            }
        )
        self.pre_computed_probs = pickle.load(
            open("python_skeleton/skeleton/pre_computed_probs.pkl", "rb")
        )

    def _process_observation(self, obs):
        res = dict()
        res["street"] = obs["street"]

        def int_to_int(x):
            return x // 10 * 9 + x % 10

        def int_to_card(x):
            return f"{x % 10}{['s', 'h', 'd'][x // 10]}"

        def ints_to_cards(l):
            return "_".join(sorted([int_to_card(i) for i in l if i != 0]))

        res["equity"] = np.array(
            [
                self.pre_computed_probs[
                    f"{ints_to_cards(obs['my_cards'])}_{ints_to_cards(obs['board_cards'])}"
                ]
            ]
        )

        res["my_cards"] = int_to_int(obs["my_cards"])
        res["board_cards"] = int_to_int(obs["board_cards"])

        res["my_pip"] = obs["my_pip"] / STARTING_STACK
        res["opp_pip"] = obs["opp_pip"] / STARTING_STACK
        res["my_stack"] = obs["my_stack"] / STARTING_STACK
        res["opp_stack"] = obs["opp_stack"] / STARTING_STACK
        res["min_raise"] = obs["min_raise"] / STARTING_STACK
        res["max_raise"] = obs["max_raise"] / STARTING_STACK

        return res

    def _process_action(self, action):
        curr_round_state = self.curr_round_state
        opp_contribution = (
            STARTING_STACK - curr_round_state.stacks[1 - curr_round_state.button % 2]
        )
        min_raise = curr_round_state.raise_bounds()[0]

        raise_amount = int(action[0] * STARTING_STACK)
        if raise_amount < opp_contribution:
            action = (2, 0)  # CheckAction()
        elif raise_amount < min_raise:
            action = (1, 0)  # CallAction()
        else:
            action = (3, raise_amount)  # RaiseAction(raise_amount)
        return action

    def step(self, action):
        action = self._process_action(action)

        obs, reward, done, trunc, info = super().step(action)
        return self._process_observation(obs), reward, done, trunc, info

    def reset(self, **kwargs):
        obs, info = super().reset(**kwargs)
        return self._process_observation(obs), info

    def _step_with_opp(self, action):
        assert self.opp_bot is not None
        assert self.curr_round_state.button % 2 == 0
        (obs1, obs2), (reward1, _), done, trunc, info = self._step_without_opp(action)
        while obs2["is_my_turn"]:
            obs2 = self._process_observation(obs2)
            action2 = self._process_action(self.opp_bot.predict(obs2)[0])
            (obs1, obs2), (reward1, _), done, trunc, info = self._step_without_opp(
                action2
            )
        return obs1, reward1, done, trunc, info

    def _validate_action(self, action, round_state, player_name: str):
        legal_actions = (
            round_state.legal_actions()
            if isinstance(round_state, RoundState)
            else {CheckAction}
        )
        if isinstance(action, RaiseAction):
            amount = int(action.amount)
            min_raise, max_raise = round_state.raise_bounds()
            if RaiseAction in legal_actions and min_raise <= amount <= max_raise:
                return action
        elif type(action) in legal_actions:
            return action
        return CheckAction() if CheckAction in legal_actions else FoldAction()
