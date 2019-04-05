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

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'

DISTANCE_MAX = 52 + 49 + 24


def init_foundation():
    return [[Card(s, v) for v in range(13)] for s in range(4)]


class ReverseSolve(object):
    def __init__(self):
        self.foundation = init_foundation()
        self.tableau = [[] for _ in range(7)]
        self.stack = []
        self.waste = []

    def get_distance(self):
        distance = sum([len(f) for f in self.foundation])
        distance += abs(49 - sum([len(t) for t in self.tableau]))
        for i, t in enumerate(self.tableau):
            for j, c in enumerate(t):
                if j < i and not c.face_up:
                    distance -= 1
        distance += abs(24 - len(self.waste) - len(self.stack))

    def reset(self):
        self.foundation = init_foundation()
        self.tableau = [[] for _ in range(7)]
        self.stack = []
        self.waste = []

    def get_valid_moves(self):
        pass


class Tableau(object):
    def __init__(self):
        self.piles = [[] for _ in range(7)]
        self.pile_distance = [i + 1 + i * 1 for i in range(7)]

    @property
    def distance(self):
        return sum(self.pile_distance)

    def add_card(self, card, col):
        self.piles[col].append(card)
        t = col + col * 1
        p = self.piles[col]
        self.pile_distance[col] = abs(t - sum(
            [2 if not c.face_up and i < col else 1 for i, c in enumerate(p)]
        ))

    def move_stack(self, from_col, start_row, to_col):
        pass


class Card(object):
    def __init__(self, suit=None, value=None, face_up=True):
        self.suit = suit
        self.value = value
        self.face_up = face_up
