"""
Simple example pokerbot, written in Python.
"""

import pickle
import random
from typing import Optional

from skeleton.actions import Action, CallAction, CheckAction, FoldAction, RaiseAction
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot
from skeleton.states import (
    BIG_BLIND,
    NUM_ROUNDS,
    SMALL_BLIND,
    STARTING_STACK,
    GameState,
    RoundState,
    TerminalState,
)


def make_key(cards: list[str], board_cards: list[str]) -> str:
    return "_".join(sorted(cards)) + "_" + "_".join(sorted(board_cards))


class Player(Bot):
    """
    A pokerbot.
    """

    def __init__(self) -> None:
        """
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        """
        self.version = "1200"

        self.evalof2 = pickle.load(open("python_skeleton/evalof2.pkl", "rb"))
        self.evalof3 = pickle.load(open("python_skeleton/evalof3.pkl", "rb"))
        self.evalof4 = pickle.load(open("python_skeleton/evalof4.pkl", "rb"))
        self.pre_all_in_eval = pickle.load(
            open("python_skeleton/skeleton/all_in_evals.pkl", "rb")
        )

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
        self.log = [self.version]
        self.log.append("================================")
        self.log.append(f"Round #{game_state.round_num}")

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
        self.log.append(f"My delta: {terminal_state.deltas[active]}")
        previous_state = terminal_state.previous_state
        self.log.append(f"Opponent cards: {previous_state.hands[1]}")
        self.log.append(f"\n")
        # self.log.append("================================\n")

        return self.log

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
        my_contribution = (
            STARTING_STACK - observation["my_stack"]
        )  # the number of chips you have contributed to the pot
        opp_contribution = (
            STARTING_STACK - observation["opp_stack"]
        )  # the number of chips your opponent has contributed to the pot
        continue_cost = (
            observation["opp_pip"] - observation["my_pip"]
        )  # the number of chips needed to stay in the pot

        self.log.append("My cards: " + str(observation["my_cards"]))
        self.log.append("Board cards: " + str(observation["board_cards"]))
        self.log.append("My stack: " + str(observation["my_stack"]))
        self.log.append("My contribution: " + str(my_contribution))
        self.log.append("My bankroll: " + str(observation["my_bankroll"]))

        # Handles all-in situations
        if observation["opp_stack"] == 0:
            # opponent has all-in
            action = self.get_action_all_in(observation)

        else:

            if len(observation["board_cards"]) == 0:
                temp_cards_list = observation["my_cards"]
                temp_cards_list_s = sorted(
                    temp_cards_list, key=lambda x: (int(x[0]), x[1])
                )
                key = temp_cards_list_s[0] + "_" + temp_cards_list_s[1]
                equity = self.evalof2[key]

            if len(observation["board_cards"]) == 1:
                temp_cards_list = observation["my_cards"] + observation["board_cards"]
                temp_cards_list_s = sorted(
                    temp_cards_list, key=lambda x: (int(x[0]), x[1])
                )
                key = (
                    temp_cards_list_s[0]
                    + "_"
                    + temp_cards_list_s[1]
                    + "_"
                    + temp_cards_list_s[2]
                )
                equity = self.evalof3[key]

            if len(observation["board_cards"]) == 2:
                temp_cards_list = observation["my_cards"] + observation["board_cards"]
                temp_cards_list_s = sorted(
                    temp_cards_list, key=lambda x: (int(x[0]), x[1])
                )
                key = (
                    temp_cards_list_s[0]
                    + "_"
                    + temp_cards_list_s[1]
                    + "_"
                    + temp_cards_list_s[2]
                    + "_"
                    + temp_cards_list_s[3]
                )
                equity = self.evalof4[key]

            if equity > my_contribution:
                expected_diff = equity - my_contribution
                bid_diff = opp_contribution - my_contribution
                self.log.append(f"Expected diff: {expected_diff:.2f}")
                self.log.append(f"  Actual diff: {bid_diff}")
                if (
                    bid_diff > 0.9 * expected_diff
                    and CallAction in observation["legal_actions"]
                ):
                    action = CallAction()
                if (
                    bid_diff <= 0.9 * expected_diff
                    and RaiseAction in observation["legal_actions"]
                ):
                    raise_amount = min(int(expected_diff), observation["max_raise"])
                    raise_amount = max(raise_amount, observation["min_raise"])
                    action = RaiseAction(raise_amount)
            elif CheckAction in observation["legal_actions"]:
                action = CheckAction()
            else:
                action = FoldAction()

        self.log.append(str(action) + "\n")

        return action

    def get_action_all_in(self, observation: dict) -> Action:

        cur_return = observation["my_stack"]
        my_cards_key = make_key(observation["my_cards"], observation["board_cards"])
        all_return = 2 * STARTING_STACK * self.pre_all_in_eval[my_cards_key]
        self.log.append(f"All-in return: {all_return}")
        if cur_return < all_return:
            return CallAction()
        else:
            if CheckAction in observation["legal_actions"]:
                return CheckAction()
            else:
                return FoldAction()


if __name__ == "__main__":
    run_bot(Player(), parse_args())
