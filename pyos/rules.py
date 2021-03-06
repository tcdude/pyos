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

from pyksolve import deferred, solver

import common

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2020 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'

Seed = Union[int, str, bytes, bytearray]


def shuffled_deck(random_seed=None):
    # type: (Optional[Seed]) -> Tuple[Seed, List[Tuple[int, int]]]
    """Return the used random seed and the shuffled deck."""
    seed = random_seed or os.urandom(2500)
    random.seed(seed)
    deck = [(suit, value) for suit in range(4) for value in range(13)]
    for _ in range(3):
        random.shuffle(deck)
    return seed, deck


def bonus(sec):
    """Returns the time bonus as found on Wikipedia."""
    return int(700_000 / max(30, sec))


def _convert_pyksolve(card: str) -> Tuple[int, int]:
    value, suit = card.lower()
    if value == 't':
        value = '10'
    return common.COLORS.index(suit), common.DENOMINATIONS.index(value)


class Shuffler:
    """
    Serves starting states, optionally guaranteed to be solvable.
    """
    def __init__(self):
        self._deferred_solver = deferred.DeferredSolver(threads=1, cache_num=2,
                                                        max_closed=10_000)
        self._solitaire = solver.Solitaire()

    def stop(self):
        self._deferred_solver.stop()

    @staticmethod
    def deal(random_seed=None):
        # type: (Optional[Seed]) -> Tuple[Seed, List, List]
        """
        Return the used random seed, tableau and stack.

        tableau = List[7][depth][2] => 7 Piles -> `depth` high -> card,
            open (1/0)
        stack = List[24] => card
        card = Tuple(suit, value)
        """
        seed, stack = shuffled_deck(random_seed)
        tableau = [[] for _ in range(7)]
        for start in range(7):
            first = True
            for pile in range(start, 7):
                card = stack.pop()
                tableau[pile].append([card, 1 if first else 0])
                first = False
        return seed, tableau, stack


    def winner_deal(self, random_seed=None, draw=1):
        # type: (Optional[Seed], Optional[int]) -> Tuple[Seed, List, List]
        """
        Return the used random seed, tableau and stack.

        tableau = List[7][depth][2] => 7 Piles -> `depth` high -> card, visible
        stack = List[24] => card
        card = Tuple(suit, value)
        """
        if random_seed is None:
            seed, tbl_setup, _ = self._deferred_solver.get_solved(draw)
        else:
            self._solitaire.shuffle1(random_seed)
            self._solitaire.reset_game()
            seed = random_seed
            tbl_setup = self._solitaire.game_diagram()
        piles = tbl_setup.split('\n')
        stack = []
        for card in piles[8].split(':')[1].strip().split(' '):
            stack.insert(0, _convert_pyksolve(card))
        tableau = []
        for pile in piles[1:8]:
            first = True
            tableau.append([])
            tmp = pile.split(':')[1].strip().split(' ')
            cards = [tmp[0]]
            if len(tmp) > 1:
                tmp = tmp[1].split('-')
                tmp.pop(0)
                cards += tmp
            for card in cards:
                tableau[-1].insert(0, (_convert_pyksolve(card), first))
                first = False
        return seed, tableau, stack
