import itertools
import pickle
from multiprocessing import Pool

from tqdm import tqdm


def make_key(cards: list[str], board_cards: list[str]) -> str:
    return "_".join(sorted(cards)) + "_" + "_".join(sorted(board_cards))


def get_leftover_cards(cards: list[str]) -> list[str]:
    return [
        f"{rank}{suit}"
        for rank in "123456789"
        for suit in "shd"
        if f"{rank}{suit}" not in cards
    ]


def get_all_cards() -> list[str]:
    return get_leftover_cards([])


def compute_all_in_payoff(
    my_cards: list[str],
    board_cards: list[str],
    probs: dict[str, float],
    cutoff: float,
) -> float:

    leftover_cards = get_leftover_cards(list(my_cards) + list(board_cards))
    possible_opp_card = list(itertools.permutations(leftover_cards, 2))
    opp_equity_keys = [
        make_key(opp_cards, board_cards) for opp_cards in possible_opp_card
    ]
    opp_equity = sorted([probs[opp_equity_key] for opp_equity_key in opp_equity_keys])
    opp_equity = opp_equity[-int(len(opp_equity) * cutoff) :]

    my_equity_key = make_key(my_cards, board_cards)
    my_equity = probs[my_equity_key]
    shares = [
        my_equity / (probs[opp_equity_key] + my_equity)
        if (probs[opp_equity_key] + my_equity) > 1e-8
        else 0.5
        for opp_equity_key in opp_equity_keys
        # if probs[opp_equity_key] > cutoff
    ]
    return sum(shares) / len(shares)


def compute_all_in_payoff_wrapper(args) -> float:
    return compute_all_in_payoff(*args)


def compute_all_in_with_known_info(prob_file_in: str, eval_file_out: str):

    probs = pickle.load(open(prob_file_in, "rb"))
    all_cards = get_all_cards()
    todos = {}

    for my_cards in tqdm(itertools.permutations(all_cards, 2)):
        leftover_cards = get_leftover_cards(my_cards)
        for board_cards in itertools.chain(
            [tuple()],
            [(card,) for card in leftover_cards],
            itertools.permutations(leftover_cards, 2),
        ):
            todos[make_key(my_cards, board_cards)] = (my_cards, board_cards, probs)

    print(len(todos))
    todos = list(todos.values())

    for cutoff in range(1, 11):
        P = Pool(20)
        res = P.map_async(
            compute_all_in_payoff_wrapper, [x + (cutoff / 10,) for x in todos]
        ).get()
        P.close()
        P.join()
        res = {
            make_key(my_cards, board_cards): share
            for ((my_cards, board_cards, _), share) in zip(todos, res)
        }

        with open(eval_file_out.replace(".pkl", f"_{cutoff}.pkl"), "wb") as fout:
            pickle.dump(res, fout)


if __name__ == "__main__":
    compute_all_in_with_known_info(
        "skeleton/pre_computed_probs.pkl", "skeleton/all_in_evals.pkl"
    )
