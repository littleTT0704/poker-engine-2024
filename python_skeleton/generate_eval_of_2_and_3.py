"""
Simple example pokerbot, written in Python.
"""
import numpy as np
import itertools
import pickle
from typing import Optional

from skeleton.actions import Action, CallAction, CheckAction, FoldAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot
from skeleton.evaluate import evaluate
from itertools import combinations

def find_combinations(lst, k):
    return list(combinations(lst, k))


def normalize_values(data_dict):
    # Define the new minimum and maximum values
    new_min = 0
    new_max = 400
    old_min = min(data_dict.values())
    old_max = max(data_dict.values())
    scaling_factor = (new_max - new_min) / (old_max - old_min)
    normalized_dict = {key: new_min + (value - old_min) * scaling_factor for key, value in data_dict.items()}
    return normalized_dict

pre_computed_evals = pickle.load(open("pre_computed_evals.pkl", "rb")) 
pre_computed_evals = normalize_values(pre_computed_evals)
cards = [f"{rank}{suit}" for rank in "123456789" for suit in "shd"]

def generate_evaluation_of_3cards(cards):
    three_cards_combinations = find_combinations(cards, 3)
    three_cards_evaluation = dict()
    for comb3 in three_cards_combinations:
        # find what's left
        remain_cards = set(cards)
        (card1, card2, card3) = comb3
        for card in comb3:
            remain_cards.remove(card)
        # find ultimate values
        find_eval = 0
        count = 0
        # find the sorted version of the given 3 cards
        new_key_raw = [card1,card2 ,card3]
        new_key_raw_s = sorted(new_key_raw, key=lambda x: (int(x[0]), x[1]))
        new_key = new_key_raw_s[0] + "_" + new_key_raw_s[1] + "_" + new_key_raw_s[2]
        for new_card in remain_cards:
            final_combination = [card1,card2 ,card3, new_card]
            final_combination_s = sorted(final_combination, key=lambda x: (int(x[0]), x[1]))
            final_combination_str = final_combination_s[0] + "_" + final_combination_s[1] + "_" + final_combination_s[2] + "_" + final_combination_s[3] 
            find_eval += pre_computed_evals[final_combination_str]
            count += 1
        three_cards_evaluation[new_key] = find_eval/count
    return three_cards_evaluation


def generate_evaluation_of_2cards(cards):
    two_cards_combinations = find_combinations(cards, 2)
    two_cards_evaluation = dict()
    for comb2 in two_cards_combinations:
        # find what's left
        remain_cards = set(cards)
        (card1, card2) = comb2
        for card in comb2:
            remain_cards.remove(card)
        # find ultimate values
        find_eval = 0
        count = 0
        # find the sorted version of the given 3 cards
        new_key_raw = [card1,card2]
        new_key_raw_s = sorted(new_key_raw, key=lambda x: (int(x[0]), x[1]))
        new_key = new_key_raw_s[0] + "_" + new_key_raw_s[1]
        for new_card1 in remain_cards:
            final_remain_cards = set(remain_cards)
            final_remain_cards.remove(new_card1)
            for new_card2 in final_remain_cards:
                final_combination = [card1,card2 ,new_card1, new_card2]
                final_combination_s = sorted(final_combination, key=lambda x: (int(x[0]), x[1]))
                final_combination_str = final_combination_s[0] + "_" + final_combination_s[1] + "_" + final_combination_s[2] + "_" + final_combination_s[3] 
                find_eval += pre_computed_evals[final_combination_str]
                count += 1
        two_cards_evaluation[new_key] = find_eval/count


    return two_cards_evaluation

evalof2 = generate_evaluation_of_2cards(cards)
evalof3 = generate_evaluation_of_3cards(cards)
evalof4 = pre_computed_evals

with open("evalof2.pkl", "wb") as file:
    pickle.dump(evalof2, file)

with open("evalof3.pkl", "wb") as file:
    pickle.dump(evalof3, file)

with open("evalof4.pkl", "wb") as file:
    pickle.dump(evalof4, file)