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
import logging

from table import Table

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.1'


def try_tableau(t):
    # type: (Table) -> bool
    res = False
    while True:
        if not t.tableau_to_foundation():
            break
        else:
            res = True
    tableaus = [t.tableau[:]]
    while True:
        if not t.tableau_to_tableau():
            break
        else:
            if t.tableau in tableaus:
                break
            else:
                res = True
                tableaus.append(t.tableau[:])
    return res


def solve(random_seed=None):
    t = Table()
    t.deal(random_seed)
    while not t.win_condition:
        try_tableau(t)
        while t.draw() not in (0, -1):
            pass
        while True:
            if t.waste_to_tableau() or t.waste_to_foundation():
                continue
            break
        if t.moves > 80000:
            break

    print(f'moves={t.moves}\nt={t.tableau}\nf={t.foundation}\ns={t.stack}\n'
          f'w={t.waste}')


if __name__ == '__main__':
    solve(42)
