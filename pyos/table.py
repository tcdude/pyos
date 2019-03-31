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
import pickle
import time

from rules import bonus
from rules import deal
from rules import valid_move

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.1'


class Table(object):
    def __init__(self):
        self.__tableau__ = [[] for _ in range(7)]
        self.__foundation__ = [[] for _ in range(4)]
        self.__stack__ = []
        self.__waste__ = []
        self.__history__ = []
        self.__start_time__ = 0.0
        self.__moves__ = 0
        self.__points__ = 0
        self.__last_move__ = 0.0
        self.__elapsed_time__ = 0.0
        self.__paused__ = False
        self.__current_seed__ = None
        self.draw = self.__wrap_method__(self.__draw__)
        self.undo = self.__wrap_method__(self.__undo__)
        self.waste_to_tableau = self.__wrap_method__(self.__waste_to_tableau__)
        self.waste_to_foundation = self.__wrap_method__(
            self.__waste_to_foundation__
        )
        self.tableau_to_foundation = self.__wrap_method__(
            self.__tableau_to_foundation__
        )
        self.tableau_to_tableau = self.__wrap_method__(
            self.__tableau_to_tableau__
        )
        self.foundation_to_tableau = self.__wrap_method__(
            self.__foundation_to_tableau__
        )

    @property
    def log(self):
        return logging

    @property
    def tableau(self):
        return self.__tableau__

    @property
    def foundation(self):
        return self.__foundation__

    @property
    def stack(self):
        return self.__stack__

    @property
    def waste(self):
        return self.__waste__

    @property
    def history(self):
        return self.__history__

    @property
    def waste_card(self):
        return self.__waste__[-1] if self.__waste__ else None

    @property
    def moves(self):
        return self.__moves__

    @property
    def time(self):
        return time.perf_counter() - self.__start_time__

    @property
    def points(self):
        return self.__points__

    @property
    def result(self):
        if not self.win_condition:
            raise ValueError('only available when win_condition is True')
        t = self.__last_move__ - self.__start_time__
        b = bonus(t)
        return t, self.points, b, self.moves

    @property
    def win_condition(self):
        return True if sum([len(f) for f in self.foundation]) == 52 else False

    def deal(self, random_seed=None):
        self.__current_seed__, self.__tableau__, self.__stack__ = deal(
            random_seed
        )

    def start(self):
        self.__start_time__ = time.perf_counter()
        self.__moves__ = 0

    def pause(self):
        if self.__paused__:
            return
        self.__elapsed_time__ = self.time
        self.__paused__ = True

    def resume(self):
        if not self.__paused__:
            return
        self.__start_time__ = time.perf_counter() - self.__elapsed_time__
        self.__paused__ = False

    def increment_moves(self):
        self.__moves__ += 1
        self.__last_move__ = time.perf_counter()

    def get_state(self):
        self.pause()
        return pickle.dumps((
            self.stack,
            self.waste,
            self.foundation,
            self.tableau,
            self.points,
            self.__elapsed_time__,
            self.__current_seed__,
            self.__history__
        ))

    def set_state(self, state):
        self.__stack__, self.__waste__, self.__foundation__, self.__tableau__,\
            self.__points__, self.__elapsed_time__, self.__current_seed__, \
            self.__history__ = pickle.loads(state)
        self.__paused__ = True

    def __wrap_method__(self, m):
        def wrapper(*args, **kwargs):
            self.increment_moves()
            return m(*args, **kwargs)
        return wrapper

    def __waste_to_tableau__(self, col=None):
        """Return True if valid, otherwise False"""
        wc = self.waste_card
        if wc is None:
            self.__moves__ -= 1
            self.log.info('no waste card')
            return False
        suit, value = wc
        en = list(enumerate(
            self.tableau if col is None else [self.tableau[col]]
        ))
        for i, pile in en:
            king_empty = not pile and value == 12
            match = len(pile) > 0 and valid_move(wc, pile[-1][0])
            if king_empty or match:
                ii = col or i
                self.tableau[ii].append([wc, 1])
                self.waste.pop()
                self.history.append(('w', f't{ii}', wc))
                self.__points__ += 5
                self.log.info('valid move found')
                return True
        self.__moves__ -= 1
        self.log.info('no valid move found')
        return False

    def __waste_to_foundation__(self, col=None):
        """Return True if valid, otherwise False"""
        wc = self.waste_card
        if wc is None:
            self.__moves__ -= 1
            self.log.info('no waste card')
            return False
        suit, value = wc
        en = list(enumerate(
            self.foundation if col is None else [self.foundation[col]]
        ))
        for i, pile in en:
            is_ace = not pile and value == 0
            match = len(pile) > 0 and valid_move(wc, pile[-1], True)
            if is_ace or match:
                ii = col or i
                self.foundation[ii].append(wc)
                self.waste.pop()
                self.history.append(('w', f'f{ii}', wc))
                self.__points__ += 10
                self.log.info('valid move found')
                return True
        self.__moves__ -= 1
        self.log.info('no valid move found')
        return False

    def __tableau_to_foundation__(self, col=None, fcol=None):
        """Return True if valid, otherwise False"""
        if col is None:
            en_t = list(enumerate(self.tableau))
        else:
            if len(self.tableau[col]):
                en_t = [(col, self.tableau[col])]
            else:
                self.__moves__ -= 1
                return False
        if fcol is None:
            en_f = list(enumerate(self.foundation))
        else:
            if len(self.foundation[fcol]):
                en_f = [(fcol, self.foundation[fcol])]
            else:
                self.__moves__ -= 1
                return False
        for ti, tab in en_t:
            card = tab[-1][0]
            self.log.debug(f'testing ({card})')
            for fi, fnd in en_f:
                is_ace = not fnd and card[1] == 0
                match = len(fnd) > 0 and valid_move(card, fnd[-1], True)
                self.log.debug(f'is_ace {is_ace}, match {match}')
                if is_ace or match:
                    tii = col or ti
                    fii = fcol or fi
                    self.foundation[fii].append(card)
                    self.tableau[tii].pop()
                    self.history.append((f't{tii}', f'f{fii}', card))
                    self.__points__ += 10
                    self.log.info('valid move found')
                    return True
        self.__moves__ -= 1
        self.log.info('no valid move found')
        return False

    def __tableau_to_tableau__(self, scol=None, ecol=None, srow=-1):
        """Return True if valid, otherwise False"""
        if scol is None:
            en_s = list(enumerate(self.tableau))
        else:
            en_s = [(scol, self.tableau[scol])]
        if ecol is None:
            en_e = list(enumerate(self.tableau))
        else:
            en_e = [(scol, self.tableau[ecol])]

        for si, stab in en_s:
            card = stab[srow][0]
            self.log.debug(f'testing ({card})')
            for ei, etab in en_e:
                if si == ei:
                    continue
                is_king = not etab and card[1] == 12
                match = len(etab) > 0 and valid_move(card, etab[-1][0])
                self.log.debug(
                    f'is_king {is_king}, match {match}, check against '
                    f'({etab[-1][0] if len(etab) else "empty"})'
                )
                self.log.debug(ei)
                if is_king or match:
                    sii = scol or si
                    eii = ecol or ei
                    cards = []
                    for c in stab[srow:]:
                        self.tableau[eii].append(c)
                        cards.append(c[0])
                    for _ in range(len(stab[srow:])):
                        self.tableau[sii].pop()
                    self.history.append((f't{sii}', f't{eii}', cards))
                    self.log.info('valid move found')
                    return True
        self.__moves__ -= 1
        self.log.info('no valid move found')
        return False

    def __foundation_to_tableau__(self, col, tcol=None):
        """Return True if valid, otherwise False"""
        if not self.foundation[col]:
            self.__moves__ -= 1
            return False
        en_t = list(enumerate(
            self.tableau if tcol is None else [self.tableau[tcol]]
        ))
        card = self.foundation[col][-1]
        for ti, tab in en_t:
            is_king = not tab and card[1] == 12
            match = len(tab) > 0 and valid_move(card, tab[-1][0])
            if is_king or match:
                tii = tcol or ti
                self.foundation[col].pop()
                self.tableau[tii].append([card, 1])
                self.history.append((f'f{col}', f't{tii}', card))
                self.__points__ = max(0, self.points - 15)
                self.log.info('valid move found')
                return True
        self.__moves__ -= 1
        self.log.info('no valid move found')
        return False

    def __draw__(self, draw_one=True):
        """Return int where 0 = draw, 1 = reset stack, -1 = empty"""
        if not self.stack:
            if not self.waste:
                self.__moves__ -= 1
                self.log.info('no more cards')
                return -1
            self.__stack__ = list(reversed(self.waste))
            self.__waste__ = []
            self.__points__ -= 100 if draw_one else 0
            self.__points__ = max(self.points, 0)
            self.log.info('reset stack')
            return 1
        for _ in range(1 if draw_one else 3):
            if self.stack:
                self.waste.append(self.stack.pop())
            else:
                break
        self.log.info('draw successful')
        return 0

    def __undo__(self):
        if not self.history:
            raise ValueError('history is empty')
        dest, orig, card = self.history.pop()
        self.__points__ = max(0, self.points - 15)
        if dest == 's':
            if not self.waste:
                raise ValueError('cannot undo action, Waste is empty')
            self.stack.append(self.waste.pop())
            return True
        elif dest == 'w':
            if orig[0] == 'f':
                c = self.foundation[int(orig[1])].pop()
            elif orig[0] == 't':
                c = self.tableau[int(orig[1])].pop()
            else:
                raise ValueError(f'cannot undo action ({(dest, orig, card)})')
            self.waste.append(c)
            return True
        elif dest[0] == 'f':
            if orig == 'w':
                c = self.waste.pop()
            elif orig[0] == 't':
                c = self.tableau[int(orig[1])].pop()
            else:
                raise ValueError(f'cannot undo action ({(dest, orig, card)})')
            self.foundation[int(dest[1])].append(c)
            return True
        elif dest[0] == 't':
            if orig == 'w':
                c = self.waste.pop()
            elif orig[0] == 'f':
                c = self.foundation[int(orig[1])].pop()
            else:
                raise ValueError(f'cannot undo action ({(dest, orig, card)})')
            self.tableau[int(dest[1])].append([c, 1])
            return True
        raise ValueError(f'action not understood ({(dest, orig, card)})')
