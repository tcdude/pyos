"""
Generates the day deal seeds file.
"""

import os
import pickle
import struct

from loguru import logger
from pyksolve import deferred

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

SEEDFILE = 'seeds.db'
OUTFILE = 'dailyseeds.bin'
NUMSEEDS = 26000


def write_outfile(seeds_one, seeds_three):
    """Write into packed file using little endian."""
    sorted_one = sorted(seeds_one, key=lambda x: seeds_one[x])
    sorted_three = sorted(seeds_three, key=lambda x: seeds_three[x])
    with open(OUTFILE, 'wb') as fptr:
        for one, three in zip(sorted_one, sorted_three):
            fptr.write(struct.pack('<ii', one, three))


def main():
    """Generate winner deals"""
    seeds_one = {}
    seeds_three = {}
    if os.path.isfile(SEEDFILE):
        seeds_one, seeds_three = pickle.load(open(SEEDFILE, 'rb'))
    dsolv = deferred.DeferredSolver((1, 3), cache_num=100, threads=32,
                                    max_closed=50_000)
    while len(seeds_one) < NUMSEEDS:
        try:
            num = len(seeds_one)
            if num % 10 == 0:
                logger.info(f'[{round((num / NUMSEEDS) * 100, 1):5.1f}%] '
                            f'{num}/{NUMSEEDS}')
            res = dsolv.get_solved(1)
            if res[0] in seeds_one:
                continue
            seeds_one[res[0]] = len(seeds_one)
            while len(seeds_one) > len(seeds_three):
                res = dsolv.get_solved(3)
                if res[0] in seeds_three:
                    continue
                seeds_three[res[0]] = len(seeds_three)
        except KeyboardInterrupt:
            logger.info('Received KeyboardInterrupt, shuting down')
            break
    logger.info('Stopping solver threads')
    pickle.dump((seeds_one, seeds_three), open(SEEDFILE, 'wb'))
    dsolv.stop()
    if len(seeds_one) == len(seeds_three) == NUMSEEDS:
        logger.info('Writing output file')
        write_outfile(seeds_one, seeds_three)
    else:
        logger.info('Not enough seeds collected, exiting')

if __name__ == '__main__':
    main()
