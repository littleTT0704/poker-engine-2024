"""
CMU Poker Bot Competition Game Engine 2024
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces
from collections import deque
from .actions import (
    Action,
    CallAction,
    CheckAction,
    FoldAction,
    RaiseAction,
    TerminalState,
)
from .config import (
    BIG_BLIND,
    NUM_ROUNDS,
    SMALL_BLIND,
    STARTING_STACK,
)
from .evaluate import ShortDeck
from .roundstate import RoundState
from .gym_env import PokerEnv


def card_to_int(card: str):
    rank, suit = card[0], card[1]
    suit = {"s": 0, "h": 1, "d": 2}[suit]
    return suit * 9 + int(rank)


class MyPokerEnv(PokerEnv):
    def __init__(self, num_rounds):
        super().__init__(num_rounds, "")

        self.action_space = spaces.Box(low=0, high=1, shape=(1,))
        cards_space = spaces.MultiDiscrete([3 * 9 + 1, 3 * 9 + 1])
        self.observation_space = spaces.Dict(
            {
                "legal_actions": spaces.MultiBinary(4),
                "street": spaces.Discrete(3),
                "my_cards": cards_space,
                "board_cards": cards_space,
                "my_pip": spaces.Box(low=0, high=1, shape=(1,)),
                "opp_pip": spaces.Box(low=0, high=1, shape=(1,)),
                "my_stack": spaces.Box(low=0, high=1, shape=(1,)),
                "opp_stack": spaces.Box(low=0, high=1, shape=(1,)),
                "min_raise": spaces.Box(low=0, high=1, shape=(1,)),
                "max_raise": spaces.Box(low=0, high=1, shape=(1,)),
            }
        )

    def _process_observation(self, obs):
        res = dict()
        res["legal_actions"] = obs["legal_actions"].astype(bool)
        res["street"] = obs["street"]

        def int_to_int(x):
            return x // 10 * 9 + x % 10

        res["my_cards"] = int_to_int(obs["my_cards"])
        res["board_cards"] = int_to_int(obs["board_cards"])

        res["my_pip"] = obs["my_pip"] / STARTING_STACK
        res["opp_pip"] = obs["opp_pip"] / STARTING_STACK
        res["my_stack"] = obs["my_stack"] / STARTING_STACK
        res["opp_stack"] = obs["opp_stack"] / STARTING_STACK
        res["min_raise"] = obs["min_raise"] / STARTING_STACK
        res["max_raise"] = obs["max_raise"] / STARTING_STACK

        return res

    def step(self, action):
        curr_round_state = self.curr_round_state
        opp_pip = curr_round_state.pips[1 - curr_round_state.button % 2]
        min_raise = curr_round_state.raise_bounds()[0]

        raise_amount = int(action[0] * STARTING_STACK)
        if raise_amount < opp_pip:
            action = CheckAction()
        elif raise_amount < min_raise:
            action = CallAction()
        else:
            action = RaiseAction(raise_amount)

        obs, reward, done, trunc, info = super().step(action)
        return self._process_observation(obs), reward, done, trunc, info

    def reset(self, **kwargs):
        obs, info = super().reset(**kwargs)
        return self._process_observation(obs), info
