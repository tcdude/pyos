"""
Copyright (c) 2020 Tiziano Bettio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
from typing import Optional, Union, Tuple, List
import random

from solver import ReverseSolve

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2020 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'

Seed = Union[int, str, bytes, bytearray]


def shuffled_deck(random_seed=None):
    # type: (Optional[Seed]) -> Tuple[Seed, List[Tuple[int, int]]]
    """Return the used random seed and the shuffled deck."""
    s = random_seed or os.urandom(2500)
    random.seed(s)
    deck = [(s, v) for s in range(4) for v in range(13)]
    for _ in range(3):
        random.shuffle(deck)
    return s, deck


def deal(random_seed=None):
    # type: (Optional[Seed]) -> Tuple[Seed, List, List]
    """
    Return the used random seed, tableau and stack.

    tableau = List[7][depth][2] => 7 Piles -> `depth` high -> card, open (1/0)
    stack = List[24] => card
    card = Tuple(suit, value)
    """
    s, stack = shuffled_deck(random_seed)
    tableau = [[] for _ in range(7)]
    for start in range(7):
        first = True
        for t in range(start, 7):
            c = stack.pop()
            tableau[t].append([c, 1 if first else 0])
            first = False
    return s, tableau, stack


def winner_deal(random_seed=None, draw=1):
    # type: (Optional[Seed], Optional[int]) -> Tuple[Seed, List, List]
    """
    Return the used random seed, tableau and stack.

    tableau = List[7][depth][2] => 7 Piles -> `depth` high -> card, open (1/0)
    stack = List[24] => card
    card = Tuple(suit, value)
    """
    s = random_seed or os.urandom(16)
    rs = ReverseSolve(draw, s)
    unsolved = True
    while unsolved:
        try:
            rs.solve()
        except RuntimeError:
            rs = ReverseSolve(draw, rs.r.getrandbits(2500))
        else:
            unsolved = False
    stack = [c.tup for c in rs.waste.stack]
    tableau = [[[c.tup, 1 if c.face_up else 0] for c in p] for p in rs.tableau]
    for i in range(7):
        if not tableau[i][i][1]:
            tableau[i][i][1] = 1
    # s, stack = shuffled_deck(random_seed)
    # tableau = [[] for _ in range(7)]
    # for start in range(7):
    #     first = True
    #     for t in range(start, 7):
    #         c = stack.pop()
    #         tableau[t].append([c, 1 if first else 0])
    #         first = False
    return s, tableau, stack


def valid_move(card_from, card_to, to_foundation=False):
    """Return True if the move is valid, otherwise False"""
    sf, vf = card_from
    if to_foundation:
        if vf == 0 and card_to is None:
            # Ace to empty Foundation
            return True
        if card_to is None:
            return False
    if not to_foundation and card_to is None:
        # King to empty Tableau Pile
        return True if vf == 12 else False
    st, vt = card_to
    if to_foundation and sf == st and vf - vt == 1:
        # Valid Move to Foundation
        return True
    if not to_foundation and vt - vf == 1 and sf % 2 != st % 2:
        # Valid Move to Tableau
        return True
    return False


def bonus(t):
    return int(700_000 / max(30, t))
