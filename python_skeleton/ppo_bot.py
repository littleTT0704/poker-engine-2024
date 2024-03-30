from stable_baselines3 import PPO

import pickle
import numpy as np
from typing import Optional

try:
    from skeleton.actions import (
        Action,
        CallAction,
        CheckAction,
        FoldAction,
        RaiseAction,
    )
except ImportError:
    import sys

    sys.path.append("./python_skeleton")
    from skeleton.actions import (
        Action,
        CallAction,
        CheckAction,
        FoldAction,
        RaiseAction,
    )
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot


def card_to_int(card: str):
    rank, suit = card[0], card[1]
    suit = {"s": 0, "h": 1, "d": 2}[suit]
    return suit * 9 + int(rank)


def cards_to_array(cards):
    res = np.zeros(2, dtype=int)
    for i, card in enumerate(cards):
        res[i] = card_to_int(card)
    return res


class PPOBot(Bot):
    """
    A pokerbot.
    """

    def __init__(self, model_path: str) -> None:
        """
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        """
        self.log = []
        self.pre_computed_probs = pickle.load(
            open("python_skeleton/skeleton/pre_computed_probs.pkl", "rb")
        )
        self.model = PPO.load(model_path)

    def handle_new_round(
        self, game_state: GameState, round_state: RoundState, active: int
    ) -> None:
        """
        Called when a new round starts. Called NUM_ROUNDS times.

        Args:
            game_state (GameState): The state of the game.
            round_state (RoundState): The state of the round.
            active (int): Your player's index.

        Returns:
            None
        """
        # my_bankroll = game_state.bankroll # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        # game_clock = game_state.game_clock # the total number of seconds your bot has left to play this game
        # round_num = game_state.round_num # the round number from 1 to NUM_ROUNDS
        # my_cards = round_state.hands[0] # your cards
        # big_blind = bool(active) # True if you are the big blind
        self.log = []
        self.log.append("================================")
        self.log.append("new round")
        pass

    def handle_round_over(
        self,
        game_state: GameState,
        terminal_state: TerminalState,
        active: int,
        is_match_over: bool,
    ) -> Optional[str]:
        """
        Called when a round ends. Called NUM_ROUNDS times.

        Args:
            game_state (GameState): The state of the game.
            terminal_state (TerminalState): The state of the round when it ended.
            active (int): Your player's index.

        Returns:
            Your logs.
        """
        # my_delta = terminal_state.deltas[active] # your bankroll change from this round
        # previous_state = terminal_state.previous_state # RoundState before payoffs
        # street = previous_state.street # 0, 3, 4, or 5 representing when this round ended
        # my_cards = previous_state.hands[0] # your cards
        # opp_cards = previous_state.hands[1] # opponent's cards or [] if not revealed
        self.log.append("game over")
        self.log.append("================================\n")

        return self.log

    def _process_observation(self, obs):
        res = dict()
        res["street"] = obs["street"]

        res["equity"] = np.array(
            [
                self.pre_computed_probs[
                    "_".join(sorted(obs["my_cards"]))
                    + "_"
                    + "_".join(sorted(obs["board_cards"]))
                ]
            ],
            dtype=np.float32,
        )

        res["my_cards"] = cards_to_array(obs["my_cards"])
        res["board_cards"] = cards_to_array(obs["board_cards"])

        res["my_pip"] = np.array([obs["my_pip"] / STARTING_STACK], dtype=np.float32)
        res["opp_pip"] = np.array([obs["opp_pip"] / STARTING_STACK], dtype=np.float32)
        res["my_stack"] = np.array([obs["my_stack"] / STARTING_STACK], dtype=np.float32)
        res["opp_stack"] = np.array(
            [obs["opp_stack"] / STARTING_STACK], dtype=np.float32
        )
        res["min_raise"] = np.array(
            [obs["min_raise"] / STARTING_STACK], dtype=np.float32
        )
        res["max_raise"] = np.array(
            [obs["max_raise"] / STARTING_STACK], dtype=np.float32
        )
        return res

    def _process_action(self, obs, action):
        opp_contribution = STARTING_STACK - obs["opp_stack"]
        min_raise = obs["min_raise"]

        raise_amount = int(action[0] * STARTING_STACK)
        self.log.append("Predicted raise amount: " + str(raise_amount))
        if raise_amount < opp_contribution:
            action = CheckAction()
        elif raise_amount < min_raise:
            action = CallAction()
        else:
            action = RaiseAction(raise_amount)
        return action

    def get_action(self, observation: dict) -> Action:
        """
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Args:
            observation (dict): The observation of the current state.
            {
                "legal_actions": List of the Actions that are legal to take.
                "street": 0, 1, or 2 representing pre-flop, flop, or river respectively
                "my_cards": List[str] of your cards, e.g. ["1s", "2h"]
                "board_cards": List[str] of the cards on the board
                "my_pip": int, the number of chips you have contributed to the pot this round of betting
                "opp_pip": int, the number of chips your opponent has contributed to the pot this round of betting
                "my_stack": int, the number of chips you have remaining
                "opp_stack": int, the number of chips your opponent has remaining
                "my_bankroll": int, the number of chips you have won or lost from the beginning of the game to the start of this round
                "min_raise": int, the smallest number of chips for a legal bet/raise
                "max_raise": int, the largest number of chips for a legal bet/raise
            }

        Returns:
            Action: The action you want to take.
        """
        self.log.append("My cards: " + str(observation["my_cards"]))
        self.log.append("Board cards: " + str(observation["board_cards"]))
        self.log.append("My stack: " + str(observation["my_stack"]))
        self.log.append(
            "My contribution: " + str(STARTING_STACK - observation["my_stack"])
        )
        self.log.append("My bankroll: " + str(observation["my_bankroll"]))

        obs = self._process_observation(observation)
        action = self.model.predict(obs)[0]

        action = self._process_action(observation, action)
        self.log.append(str(action) + "\n")
        return action


if __name__ == "__main__":
    run_bot(PPOBot("ppo_poker"), parse_args())
