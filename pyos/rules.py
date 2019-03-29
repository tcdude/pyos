"""
Copyright (c) 2019 Tiziano Bettio

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

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.1'

Seed = Union[int, str, bytes, bytearray]


def shuffled_deck(random_seed=None):
    # type: (Optional[Seed]) -> Tuple[Seed, List[Tuple[int, int]]]
    """Returns the used random seed and the shuffled deck."""
    s = random_seed or os.urandom(2500)
    random.seed(s)
    deck = [(s, v) for s in range(4) for v in range(13)]
    for _ in range(3):
        random.shuffle(deck)
    return s, deck


def deal(random_seed=None):
    # type: (Optional[Seed]) -> Tuple[Seed, List, List]
    """
    Returns the used random seed, tableau and stack.

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
