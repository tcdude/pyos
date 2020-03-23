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
import glob
import time
from typing import Optional, Union, Tuple, List
import random

from pyksolve import solver
try:
    import android  # pylint: disable=unused-import
    from jnius import autoclass
except ImportError:
    from subprocess import Popen, DEVNULL

import common
from service.solver import SOLUTION_PATH, STOP_FILE

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
        self._solitaire = solver.Solitaire()
        self.start_service()

    def start_service(self):
        """Start the solver service."""
        if os.path.exists(STOP_FILE):
            os.remove(STOP_FILE)
        if 'autoclass' in globals():
            service = autoclass('com.tizilogic.pyos.ServiceSolver')
            # pylint: disable=invalid-name
            mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
            # pylint: enable=invalid-name
            argument = ''
            service.start(mActivity, argument)
            print('mActivity', [i for i in dir(mActivity) if ord(i[0]) > 90],
                  '\nservice', [i for i in dir(service) if ord(i[0]) > 90],
                  '', sep='\n')
        else:
            self.stop()
            time.sleep(0.5)
            if os.path.exists(STOP_FILE):
                os.remove(STOP_FILE)
            self.__proc = Popen(['python', 'service/solver.py'],)
                                # stdout=DEVNULL, stderr=DEVNULL)

    @staticmethod
    def stop():
        """Stop the solver service."""
        with open(STOP_FILE, 'w') as fptr:
            fptr.write('1')

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

    @staticmethod
    def request_deal(draw, random_seed):
        """Request a solution of a specific deal."""
        pth = os.path.join(SOLUTION_PATH, str(draw))
        spth = os.path.join(pth, f'solution{random_seed}')
        if not os.path.exists(spth):
            rpth = os.path.join(pth, f'request{random_seed}')
            with open(rpth, 'w') as fptr:
                fptr.write('1')

    @staticmethod
    def get_solution(draw, random_seed):
        """Retrieve solution of a previously requested deal."""
        pth = os.path.join(SOLUTION_PATH, str(draw))
        spth = os.path.join(pth, f'rsolution{random_seed}')
        while True:
            if os.path.exists(spth):
                with open(spth, 'r') as fptr:
                    return fptr.read()
            time.sleep(0.001)

    def winner_deal(self, random_seed=None, draw=1):
        # type: (Optional[Seed], Optional[int]) -> Tuple[Seed, List, List]
        """
        Return the used random seed, tableau and stack.

        tableau = List[7][depth][2] => 7 Piles -> `depth` high -> card, visible
        stack = List[24] => card
        card = Tuple(suit, value)
        """
        if random_seed is None:
            seed, tbl_setup = self._get_deal(draw)
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

    def _get_deal(self, draw: int) -> Tuple[int, str]:
        pth = os.path.join(SOLUTION_PATH, str(draw))
        solutions = []
        i = 0
        while not solutions:
            solutions = glob.glob(pth + '/solution*')
            time.sleep(0.001)
            i += 1
            if i > 2000:
                self.stop()
                time.sleep(0.5)
                if os.path.exists(STOP_FILE):
                    os.remove(STOP_FILE)
                self.start_service()
                i = 0
        seed = int(solutions[0].split(pth + '/solution')[1])
        os.remove(solutions[0])
        self._solitaire.shuffle1(seed)
        self._solitaire.reset_game()
        return seed, self._solitaire.game_diagram()
