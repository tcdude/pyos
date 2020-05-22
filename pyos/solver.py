"""
Service to run pyksolve in separately from the main app.
"""

import time
import random
import traceback
from typing import Tuple
import sys

from loguru import logger
from pyksolve import solver

import common
import stats

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
__version__ = '0.3'

DRAW_COUNTS = 1, 3
CACHE_COUNT = 10
MCC = 100_000


class Solver:
    """
    Generates a configured amount of ready to use solutions in the form of files
    stored locally.
    """
    def __init__(self):
        self.solitaire = solver.Solitaire()
        self.stats = stats.Stats(common.DATAFILE)

    @logger.catch
    def run(self):
        """Run the main loop until stop is called."""
        logger.info('Solver started')
        self.stats.solver_running = True
        self.stats.exit_solver = False
        try:
            while not self.stats.exit_solver:
                if not self._generate_solution():
                    if not common.gamestate_locked():
                        self.stats.update_statistics()
                        self.stats.clean_seeds()
                    time.sleep(0.1)
        except Exception as err:  # pylint: disable=broad-except
            logger.error(f'Unhandled exception in solver {err}\n'
                         f'{traceback.format_exc()}')
        finally:
            self.stats.solver_running = False
            self.stats.exit_confirm = True

    def _generate_solution(self) -> bool:
        seed, draw_count, req = self.get_next()
        if draw_count:
            if seed:
                self.solitaire.shuffle1(seed)
            else:
                seed = self.solitaire.shuffle1(random.randint(1, 2**31 - 1))
            rep = f'draw={draw_count} seed={seed} request={req}'
            logger.debug(f'Solving {rep}')
            i = 1
            while True:
                self.solitaire.reset_game()
                mcc = MCC * i
                res = abs(self.solitaire.solve_fast(max_closed_count=mcc).value)
                if res == 1:
                    self.stats.update_seed(draw_count, seed,
                                           self.solitaire.moves_made())
                    logger.debug(f'Solution found for: {rep}')
                    break
                if req:  # A request must be solvable, improve chances
                    i += 1
                else:
                    logger.debug(f'No Solution found after {MCC} states '
                                 f'for: {rep}')
                    break
            return True
        return False

    def get_next(self) -> Tuple[int, int, bool]:
        """Retrieves the next seed/draw_count pair to solve."""
        for draw, seed in self.stats.solutions_needed:
            logger.debug(f'Got solution request, draw={draw} req={seed}')
            return seed, draw, True
        seedcount = self.stats.seed_count
        for draw in seedcount:
            if seedcount[draw] < 10:
                logger.debug(f'Not enough seeds for draw={draw}')
                return 0, draw, False
        return 0, 0, False


if __name__ == '__main__':
    logger.remove()
    try:
        import android  # pylint: disable=unused-import
        logger.add(sys.stderr, level='INFO')
    except ImportError:
        logger.add(sys.stderr, level='DEBUG')
    Solver().run()
