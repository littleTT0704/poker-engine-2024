"""
Simple example pokerbot, written in Python.
"""

import pickle
import random
from typing import Optional

from helper import make_key
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
import math



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
        self.version = "0133"

        self.evalof2 = pickle.load(open("python_skeleton/evalof2.pkl", "rb"))
        self.evalof3 = pickle.load(open("python_skeleton/evalof3.pkl", "rb"))
        self.evalof4 = pickle.load(open("python_skeleton/evalof4.pkl", "rb"))
        self.pre_all_in_eval = pickle.load(
            open("python_skeleton/skeleton/all_in_evals.pkl", "rb")
        )
        self.history_bank_roll = []
        self.lookback = 5

        self.risk_preference = 0.1 # use to adjust th tanh range 
        # currently the tanh is -0.5 to 0.5 as we - 0.5 from the result.
        # therefore, the range of risk taking will be 0.8 to 1.2, 
        # where 0.8 means very cautious and 1.2 means very aggressive
    
    def tanh(self, x):
        exp_x = math.exp(x)
        exp_neg_x = math.exp(-x)
        # Implement the formula for tanh
        return (exp_x - exp_neg_x) / (exp_x + exp_neg_x)

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
        self.log.append("new round")

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
    
    def numb_wins(self,numbers):
        wins = 0
        for i in range(1, len(numbers)):
            difference = numbers[i] - numbers[i - 1]
            if difference >= 0:
                sign = 1
            else:
                sign = 0
            wins += sign
        
        return wins

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

        # Record the most recent 11 bankroll to get the win/loss of most recent 10 games
        mang = 1
        self.history_bank_roll.append(observation["my_bankroll"])
        if len(self.history_bank_roll) >= self.lookback:
            past_games = self.history_bank_roll[-self.lookback:]
            most_recent_wins = self.numb_wins(past_games)
            most_recent_winning_rate = most_recent_wins/(self.lookback-1)

            deviated_winning_rate = most_recent_winning_rate - 0.5 # -0.5 to 0.5



            mang += (self.tanh(deviated_winning_rate)) * self.risk_preference
            # print(past_games)
            # print("winning rate", most_recent_winning_rate)
            # print("deviated_winning_rate", deviated_winning_rate)
            # print("tanh result", self.tanh(deviated_winning_rate))
            
            # print("adj on mang", (self.tanh(deviated_winning_rate)) * self.risk_preference)
            # print("mang", mang)
            


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
                if (
                    bid_diff > 0.9 * expected_diff * min(1, mang)
                    and CallAction in observation["legal_actions"]
                ):
                    action = CallAction()
                if (
                    bid_diff <= 0.9 * expected_diff
                    and RaiseAction in observation["legal_actions"]
                ):
                    raise_amount = min(int(expected_diff*mang), observation["max_raise"])
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
        if cur_return < all_return:
            return CallAction()
        else:
            if CheckAction in observation["legal_actions"]:
                return CheckAction()
            else:
                return FoldAction()


if __name__ == "__main__":
    run_bot(Player(), parse_args())
