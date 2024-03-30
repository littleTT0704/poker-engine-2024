"""
Simple example pokerbot, written in Python.
"""
import pickle
import random
from typing import Optional

from skeleton.actions import Action, CallAction, CheckAction, FoldAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

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
        self.log = []
        self.pre_computed_probs = pickle.load(open("python_skeleton/skeleton/pre_computed_probs.pkl", "rb")) 
        pass

    def handle_new_round(self, game_state: GameState, round_state: RoundState, active: int) -> None:
        """
        Called when a new round starts. Called NUM_ROUNDS times.
        
        Args:
            game_state (GameState): The state of the game.
            round_state (RoundState): The state of the round.
            active (int): Your player's index.

        Returns:
            None
        """
        #my_bankroll = game_state.bankroll # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        #game_clock = game_state.game_clock # the total number of seconds your bot has left to play this game
        #round_num = game_state.round_num # the round number from 1 to NUM_ROUNDS
        #my_cards = round_state.hands[0] # your cards
        #big_blind = bool(active) # True if you are the big blind
        self.log = []
        self.log.append("================================")
        self.log.append("new round")
        pass

    def handle_round_over(self, game_state: GameState, terminal_state: TerminalState, active: int, is_match_over: bool) -> Optional[str]:
        """
        Called when a round ends. Called NUM_ROUNDS times.

        Args:
            game_state (GameState): The state of the game.
            terminal_state (TerminalState): The state of the round when it ended.
            active (int): Your player's index.

        Returns:
            Your logs.
        """
        #my_delta = terminal_state.deltas[active] # your bankroll change from this round
        #previous_state = terminal_state.previous_state # RoundState before payoffs
        #street = previous_state.street # 0, 3, 4, or 5 representing when this round ended
        #my_cards = previous_state.hands[0] # your cards
        #opp_cards = previous_state.hands[1] # opponent's cards or [] if not revealed
        self.log.append("game over")
        self.log.append("================================\n")

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
        my_contribution = STARTING_STACK - observation["my_stack"] # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - observation["opp_stack"] # the number of chips your opponent has contributed to the pot
        continue_cost = observation["opp_pip"] - observation["my_pip"] # the number of chips needed to stay in the pot

        bet = 2
        equity = self.pre_computed_probs['_'.join(sorted(observation["my_cards"])) + '_' + '_'.join(sorted(observation["board_cards"]))]
        # print("bet106", equity)
        rule1 = equity*(my_contribution+opp_contribution)-my_contribution
        bet += rule1
        # print("bet108", bet)
        
        rule2 = 0.05*(opp_contribution**3)/((my_contribution+opp_contribution)**2) # be tighter by 0.01
        bet -= rule2
        # print("bet112", bet)

        bluff_prob = random.random()/3
        if random.random() <= bluff_prob: bet *= 50*max((equity-0.5)**2, 0)
        # print("bet116", bet)

        # print("bet118", bet)
        self.log.append(f"Premeta bet: {bet}")

        ev = equity*opp_contribution-(1-equity)*bet
        var = equity*(opp_contribution-ev)**2+(1-equity)*(-bet-ev)**2
        meta = 0.1*var**0.5
        # bet -= 0.1*meta
        # print("bet126", bet)

        self.log.append(f"Bet steps: {rule1, rule2, meta}")

        self.log.append("My cards: " + str(observation["my_cards"]))
        self.log.append("Board cards: " + str(observation["board_cards"]))
        self.log.append("My stack: " + str(observation["my_stack"]))
        self.log.append("My contribution: " + str(my_contribution))
        self.log.append("My bankroll: " + str(observation["my_bankroll"]))

        if CheckAction in observation["legal_actions"]:
            # print("bet145", bet)
            return CheckAction()
        if bet >= continue_cost:
            # print("bet137", bet)
            if bet >= observation["min_raise"] and RaiseAction in observation["legal_actions"]:
                # print("bet139", bet)
                return RaiseAction(round(min(bet, observation["max_raise"])))
            if bet <= observation["min_raise"] and CallAction in observation["legal_actions"]:
                # print("bet142", bet)
                return CallAction()
        # print("bet147", bet)
        return FoldAction()


if __name__ == '__main__':
    run_bot(Player(), parse_args())