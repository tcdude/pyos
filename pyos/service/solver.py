"""
Service to run pyksolve in separately from the main app.
"""

import os
import glob
import time
import random
from typing import Tuple

from loguru import logger
from pyksolve import solver

__author__ = 'Tiziano Bettio'
__copyright__ = """
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

__license__ = 'MIT'
__version__ = '0.2'

STOP_FILE = 'cache/solutions/stop'
SOLUTION_PATH = 'cache/solutions'
DRAW_COUNTS = 1, 3
CACHE_COUNT = 10
MCC = 100_000

if not os.path.exists(SOLUTION_PATH):
    os.makedirs(SOLUTION_PATH)


class Solver:
    """
    Generates a configured amount of ready to use solutions in the form of files
    stored locally.
    """
    def __init__(self):
        self.solitaire = solver.Solitaire()
        self.__active = False
        for i in glob.glob(SOLUTION_PATH + '/*/rsolution*'):
            os.remove(i)

    def run(self):
        """Run the main loop until stop is called."""
        self.__active = True
        while self.__active:
            if os.path.exists(STOP_FILE):
                os.remove(STOP_FILE)
                break
            self._generate_solution()
            time.sleep(0.1)

    def _generate_solution(self):
        seed, draw_count, req = self.get_next()
        if draw_count:
            if seed:
                self.solitaire.shuffle1(seed)
            else:
                seed = self.solitaire.shuffle1(random.randint(1, 2**31 - 1))
            logger.debug(f'Solving draw={draw_count} seed={seed}')
            i = 1
            while True:
                self.solitaire.reset_game()
                mcc = MCC * i
                res = abs(self.solitaire.solve_fast(max_closed_count=mcc).value)
                if res == 1:
                    pth = os.path.join(SOLUTION_PATH, str(draw_count))
                    fpth = f'rsolution{seed}' if req else f'solution{seed}'
                    pth = os.path.join(pth, fpth)
                    logger.debug(f'Solution found draw={draw_count} '
                                 f'seed={seed}')
                    with open(pth, 'w') as fptr:
                        fptr.write(self.solitaire.moves_made())
                    break
                if req:  # A request must be solvable, improve chances
                    i += 1
                else:
                    break

    @staticmethod
    def get_next() -> Tuple[int, int, bool]:
        """Retrieves the next seed/draw_count pair to solve."""
        draws = {}
        for i in DRAW_COUNTS:
            pth = os.path.join(SOLUTION_PATH, str(i))
            if not os.path.exists(pth):
                os.makedirs(pth)
                draws[i] = CACHE_COUNT
                continue
            request = glob.glob(pth + '/request*')
            if request:
                os.remove(request[0])
                logger.debug(f'found requests, draw={i} req={request[0]}')
                return int(request[0].split('/request')[1]), i, True
            draws[i] = CACHE_COUNT - len(glob.glob(pth + '/solution*'))
        max_i = max(draws, key=lambda x: draws[x])
        if draws[max_i]:
            logger.debug(f'found no requests, solve random for draw={max_i}')
            return 0, max_i, False
        return 0, 0, False


if __name__ == '__main__':
    Solver().run()
