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
from random import Random
from typing import Any
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union


__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'

START_MAX_STEPS = 36
START_MIN_STEPS = 16
MIN_F2T = 0
BIAS = 1
DISTANCE_MAX = 52 + 49 + 48
STEP_TO_DISTANCE = 2

# Custom Types
CARD_TUPLE = Tuple[int, int]
TABLEAU_MOVES = Tuple[int, int, bool]  # (color, value, any_card)
SEED = Union[int, str, bytes, bytearray]


class ReverseSolve(object):
    """
    Generates a random, solvable Klondike/Solitaire game by assembling the
    Tableau and Stack in reverse order, avoiding redundant moves.
    """
    def __init__(self, draw=1, seed=None):
        # type: (Optional[int], Optional[SEED]) -> None
        self.draw = draw
        self.seed = seed
        self.foundation = Foundation()
        self.tableau = Tableau()
        self.waste = Waste(self.draw)
        self.history = History()
        self.r = Random(self.seed)
        self.max_steps = self.r.randint(100, 170)
        self.max_f2w = self.r.randint(4, 16)
        self.f2w_count = 0
        self.step = 0

    @property
    def distance(self):
        # type: () -> int
        ft_dist = self.foundation.distance + self.tableau.distance
        if not ft_dist:
            err = False
            while self.waste.distance:
                if err:
                    raise RuntimeError('CRITICAL! could not fill stack')
                if not self.waste.to_stack():
                    err = True
        return ft_dist + self.waste.distance

    @property
    def solved(self):
        return False if self.distance else True

    def randomize_start_position(self):
        steps = self.r.randint(5, 13)
        empty = list(range(4)) + self.r.choices(list(range(4, steps * 4)), k=3)
        f_idx = [0, 1, 2, 3]
        t_idx = f_idx + [4, 5, 6]
        must_empty = 0
        for i in range(steps):
            must_empty += sum(
                [1 for v in range(i * 4, i * 4 + 4) if v in empty]
            )
            add_count = 0
            while add_count < 4:
                self.r.shuffle(f_idx)
                for origin in f_idx:
                    if not self.foundation[origin]:
                        continue
                    card = self.foundation[origin][-1]
                    self.r.shuffle(t_idx)
                    for dest in t_idx:
                        result = self.tableau.is_valid_move(card, dest)
                        if result == 1 and not must_empty:
                            self.foundation.remove_card(card)
                            self.tableau.add_card(card, dest)
                            add_count += 1
                            break
                        elif result == 2 and must_empty:
                            self.foundation.remove_card(card)
                            self.tableau.add_card(card, dest)
                            add_count += 1
                            must_empty = max(must_empty - 1, 0)
                            break
        self.step = steps * 4
        print('randomized')
        self.print_current_position()
        print('valid moves')
        print(self.get_valid_moves())
        return

    def print_current_position(self):
        f = [str(card) for card in self.foundation.top_cards]
        print('\nFoundation')
        print(' | '.join(f))
        print('\n\nTableau')
        for row in range(max([len(p) for p in self.tableau])):
            print('| ', end='')
            for col in range(7):
                if len(self.tableau[col]) > row:
                    print(str(self.tableau[col][row]) + ' | ', end='')
                else:
                    print('     | ', end='')
            print()
        print('Stack: ', str(self.waste.stack))
        print('Waste: ', str(self.waste.waste))

    def get_valid_moves(self):
        moves = []
        f_top = self.foundation.top_cards
        t_top = self.tableau.top_cards
        self.waste_moves(moves, f_top, t_top)
        self.foundation_moves(moves, f_top, t_top)
        self.tableau_moves(moves, f_top, t_top)
        return moves

    def foundation_moves(self, moves, f_top, t_top):
        for fi, f_card in enumerate(f_top):
            if f_card is None:
                continue
            for ti, t_card in enumerate(t_top):
                if t_card is None:
                    if self.step > MIN_F2T or f_card.value == 12:
                        moves.append((f'f{fi}', f't{ti}', f_card, -2))
                    continue
                valid, _ = t_card + f_card
                pile = self.tableau[ti]
                if valid or len(pile) == 1 \
                        or (not pile[-2].face_up and len(pile) < ti + 1):
                    before = abs(ti + 1 - len(pile))
                    after = abs(ti - len(pile))
                    move = (f'f{fi}', f't{ti}', f_card, after - before)
                    moves += [move] * BIAS

    def tableau_moves(self, moves, f_top, t_top):
        # type: (list, List[Card], List[Card]) -> None

        # Tableau to Foundation
        if self.step > MIN_F2T:
            for ti, t_card in enumerate(t_top):
                if t_card is None or t_card.blocked:
                    continue
                for fi, f_card in enumerate(f_top):
                    if f_card is None:
                        continue
                    _, valid = f_card + t_card
                    pile = self.foundation[fi]
                    if valid:
                        before = abs(ti + 1 - len(pile))
                        after = abs(ti - len(pile))
                        moves.append(
                            (f'f{fi}', f't{ti}', f_card, after - before)
                        )

        # Tableau to Tableau
        if self.step > MIN_F2T:
            for s_col, s_pile in enumerate(self.tableau):
                if not s_pile:
                    continue
                for s_row, s_card in enumerate(s_pile):
                    if not s_card.face_up or s_card.blocked:
                        continue
                    for e_col, e_card in enumerate(t_top):
                        if s_col == e_col:
                            continue
                        s_len = len(s_pile)
                        if s_row <= s_len:
                            mult = BIAS * 2
                        else:
                            mult = BIAS
                        s_rows = s_row + 1
                        s_before = abs(s_col + 1 - s_len)
                        s_after = abs(s_col + 1 - (s_len - s_rows))
                        s_delta = s_after - s_before
                        pile = self.tableau[e_col]
                        e_len = len(pile)
                        e_before = abs(e_col + 1 - e_len)
                        e_after = abs(e_col + 1 - (e_len + s_rows))
                        e_delta = e_after - e_before
                        move = (
                            f't{s_col}:{s_row}', f't{e_col}',
                            s_card,
                            s_delta + e_delta
                        )
                        if e_card is None:
                            moves += [move] * mult
                            continue
                        valid, _ = e_card + s_card
                        if valid:
                            moves += [move] * mult
                            continue
                        if e_len == 1 or \
                                (not pile[-2].face_up and
                                 len(pile) < e_col + 1):
                            move = (
                                f't{s_col}:{s_row}', f't{e_col}',
                                s_card,
                                s_delta + e_delta - 1
                            )
                            moves += [move] * mult

    def waste_moves(self, moves, f_top, t_top):
        waste_full = self.waste.full
        if not waste_full:
            if self.max_f2w > self.f2w_count:
                for i, card in enumerate(f_top):
                    if card is None:
                        continue
                    moves.append((f'f{i}', 'w', card, -2))
            for i, card in enumerate(t_top):
                if card is None or card.blocked:
                    continue
                num_cards = len(self.tableau.piles[i])
                before = abs(i + 1 - num_cards)
                after = abs(i - num_cards)
                moves.append((f't{i}', 'w', card, after - before))
        if self.waste.valid_reset_waste:
            s_len = len(self.waste['stack'])
            move = ('s', 'w', None, s_len)
            moves += [move]
        if self.waste.valid_to_stack:
            move = ('w', 's', None, -self.draw)
            moves += [move] * BIAS

    def solve(self):
        if self.solved:
            return
        self.randomize_start_position()
        while not self.solved:
            moves = self.get_valid_moves()
            self.r.shuffle(moves)
            est_distance = (self.max_steps - self.step) * STEP_TO_DISTANCE
            allow_positive = True if self.distance < est_distance else False
            while True:
                if not moves:
                    raise RuntimeError('CRITICAL: No valid move was found')
                move = moves.pop()
                if move[-1] > 0 and not allow_positive:
                    continue
                if self.try_move(move):
                    self.step += 1
                    break
        print(f'solved in {self.step} steps')
        self.print_current_position()

    def try_move(self, move):
        s, e, card, cost = move
        if s.startswith('s'):
            return self.waste.reset_waste()
        elif s.startswith('w'):
            return self.waste.to_stack()
        elif s.startswith('f'):
            if e.startswith('w'):
                if not self.max_f2w > self.f2w_count:
                    return False
                rr = self.foundation.remove_card(card)
                ar = self.waste.add_card(card)
                if not (ar and rr):
                    raise ValueError(f'Could not move {str(card)} from '
                                     f'foundation to waste')
                self.f2w_count += 1
                return True
            if e.startswith('t'):
                col = int(e[1])
                if len(self.foundation[card.suit]) > 1:
                    sp = self.foundation[card.suit][-2]
                else:
                    sp = None
                if len(self.tableau[col]) > 0:
                    ep = self.tableau[col][-1]
                else:
                    ep = None
                if not self.history.add(card, sp, ep, 'f', 't'):
                    return False
                ar = self.tableau.add_card(card, col)
                if not ar:
                    return False
                rr = self.foundation.remove_card(card)
                if not (ar and rr):
                    raise ValueError(f'Could not move {str(card)} from '
                                     f'foundation to tableau rr={rr}, ar={ar}')
                return True
        elif s.startswith('t'):
            col = int(s[1])
            if e.startswith('w'):
                rr = self.tableau.remove_card(col)
                ar = self.waste.add_card(card)
                if not (ar and rr):
                    raise ValueError(f'Could not move {str(card)} from '
                                     f'tableau to waste')
                return True
            if e.startswith('f'):
                if len(self.tableau[col]) > 1:
                    sp = self.tableau[col][-2]
                else:
                    sp = None
                if len(self.foundation[card.suit]) > 0:
                    ep = self.foundation[card.suit][-1]
                else:
                    ep = None
                if not self.history.add(card, sp, ep, 't', 'f'):
                    return False
                rr = self.tableau.remove_card(col)
                ar = self.foundation.add_card(card)
                if not (ar and rr):
                    raise ValueError(f'Could not move {str(card)} from '
                                     f'tableau to waste')
                return True
            if e.startswith('t'):
                row = int(s.split(':')[1])
                e_col = int(e[1])
                if row > 0:
                    sp = self.tableau[col][row - 1]
                else:
                    sp = None
                if len(self.tableau[e_col]) > 0:
                    ep = self.tableau[e_col][-1]
                else:
                    ep = None
                if not self.history.add(card, sp, ep, 't', 't'):
                    return False
                return self.tableau.move_stack(col, row, e_col)
        raise ValueError(f'Unable to execute move {move}')


class Tableau(object):
    def __init__(self):
        self.piles = [[] for _ in range(7)]  # type: List[List[Card]]
        self.pile_distance = [2 * i + 1 for i in range(7)]

    def __getitem__(self, item):
        if isinstance(item, int) and -1 < item < 7:
            return self.piles[item]
        raise IndexError('Index out of bounds, must be between 0 and 6')

    @property
    def distance(self):
        # type: () -> int
        return sum(self.pile_distance)

    @property
    def top_cards(self):
        return [p[-1] if p else None for p in self.piles]

    def is_valid_move(self, card, col):
        """
        Return:
            0 = invalid move
            1 = valid move
            2 = valid to empty pile
            3 = valid with flip top card
        """
        if card.blocked:
            return 0
        pile = self.piles[col]
        if not pile:
            return 2
        valid, _ = pile[-1] + card
        if valid:
            return 1
        pl = len(pile)
        if pl == 1:
            if col > 0:
                return 3
            return 0
        if not pile[-2].face_up and pl < col + 1:
            return 3
        return 0

    def __update_distance__(self, col):
        # type: (int) -> None
        t = 2 * col + 1
        p = self.piles[col]
        d = 0
        for i, c in enumerate(p):
            if not c.face_up and i < col or (not col and not c.face_up):
                d += 2
            else:
                d += 1
        self.pile_distance[col] = abs(t - d)

    def add_card(self, card, col):
        # type: (Card, int) -> bool
        move_type = self.is_valid_move(card, col)
        pile = self.piles[col]
        if move_type == 2:
            if card.value != 12 or col == 0:
                card.blocked = True
        elif move_type == 3:
            # if the card was blocked to hold in place, it can now be flipped
            pile[-1].blocked = False
            pile[-1].face_up = False

        if move_type > 0:
            pile.append(card)
            self.__update_distance__(col)
        return move_type

    def move_stack(self, from_col, start_row, to_col):
        # type: (int, int, int) -> bool
        if len(self.piles[from_col]) <= start_row:
            raise ValueError(f'tableau col {from_col} has no row {start_row}')
        first_valid = False
        stack = self.piles[from_col][start_row:]
        for card in stack:
            result = self.add_card(card, to_col)
            if not result and first_valid:
                raise ValueError('tableau integrity problem')
            if not result:
                return False
            if not first_valid:
                first_valid = True
                if result == 3:
                    card.blocked = True
        for _ in range(len(stack)):
            self.remove_card(from_col)
        pile = self.piles[from_col]
        pl = len(pile)
        if pl == 1 or (1 < pl < from_col + 1 and not pile[-2].face_up):
            if not pile[-1].blocked:
                pile[-1].face_up = False
        self.__update_distance__(from_col)
        self.__update_distance__(to_col)
        return True

    def remove_card(self, col):
        # type: (int) -> bool
        pile = self.piles[col]
        if pile:
            pile.pop()
            # pl = len(pile)
            # if pl == 1 or (1 < pl < col + 1 and not pile[-2].face_up):
            #     if not pile[-1].blocked:
            #         pile[-1].face_up = False
            self.__update_distance__(col)
            return True
        return False


class Foundation(object):
    def __init__(self):
        self.piles = [
            [Card(s, v) for v in range(13)] for s in range(4)
        ]  # type: List[List[Card]]

    def __getitem__(self, item):
        if isinstance(item, int) and -1 < item < 4:
            return self.piles[item]
        raise IndexError('Index out of bounds, must be between 0 and 4')

    @property
    def distance(self):
        # type: () -> int
        return sum([len(pile) for pile in self.piles])

    @property
    def top_cards(self):
        # type: () -> List[Union[Card, None]]
        cards = []
        for pile in self.piles:
            if pile:
                cards.append(pile[-1])
            else:
                cards.append(None)
        return cards

    @property
    def valid_moves(self):
        # type: () -> List[CARD_TUPLE]
        return [(s, v + 1) for s, v in self.top_cards]

    def add_card(self, card):
        # type: (Card) -> bool
        if card.tup not in self.valid_moves:
            return False
        self.piles[card.suit].append(card)
        return True

    def remove_card(self, card):
        # type: (Card) -> bool
        if not self.piles[card.suit] or card != self.piles[card.suit][-1]:
            return False
        self.piles[card.suit].pop()
        return True


class Waste(object):
    def __init__(self, draw=1):
        self.draw = draw
        self.waste = []  # type: List[Card]
        self.stack = []  # type: List[Card]

    def __getitem__(self, item):
        if item in (0, 'w', 'waste'):
            return self.waste
        if item in (1, 's', 'stack'):
            return self.stack
        raise IndexError('Index out of bounds')

    @property
    def distance(self):
        # type: () -> int
        return abs(24 - len(self.stack) + 24 - len(self.stack) - len(self.waste))

    @property
    def full(self):
        # type: () -> bool
        return False if len(self.waste) + len(self.stack) < 24 else True

    @property
    def all_stack(self):
        # type: () -> bool
        return False if len(self.waste) else True

    @property
    def valid_to_stack(self):
        # type: () -> bool
        if self.draw == 1:
            return len(self.waste) > 0
        w_len = len(self.waste)
        tot_len = len(self.stack) + w_len
        if w_len >= self.draw or w_len == tot_len % self.draw:
            return True
        return False

    @property
    def valid_reset_waste(self):
        # type: () -> bool
        if len(self.waste) > 0 or len(self.stack) == 0:
            return False
        return True

    def add_card(self, card):
        # type: (Card) -> bool
        if self.full:
            return False
        self.waste.append(card)
        card.blocked = True
        return True

    def to_stack(self):
        # type: () -> bool
        if not self.valid_to_stack:
            return False
        if self.draw == 1:
            self.stack.append(self.waste.pop())
            return True
        w_len = len(self.waste)
        s_len = len(self.stack)
        if not s_len:
            remainder = w_len % self.draw
            if w_len and remainder:
                self.stack += list(reversed(self.waste[-remainder:]))
                self.waste = self.waste[:-remainder]
                return True
            if w_len and not remainder:
                self.stack += list(reversed(self.waste[-self.draw:]))
                self.waste = self.waste[:-self.draw]
                return True
        elif s_len and w_len >= self.draw:
            self.stack += list(reversed(self.waste[-self.draw:]))
            self.waste = self.waste[:-self.draw]
            return True
        return False

    def reset_waste(self):
        # type: () -> bool
        if not self.valid_reset_waste:
            return False
        self.waste = list(reversed(self.stack))
        return True


class Card(object):
    def __init__(self, suit=None, value=None, face_up=True):
        self.suit = suit
        self.value = value
        self.face_up = face_up
        self.blocked = False
        self.color = self.suit % 2

    @property
    def tup(self):
        # type: () -> Tuple[int, int]
        return self.suit, self.value

    def __str__(self):
        # return f'{self.suit}{self.value:02d}{"u" if self.face_up else "d"}'
        return self.repr()

    def __repr__(self):
        # return f'{self.suit}{self.value:02d}{"u" if self.face_up else "d"}'
        return self.repr()

    def repr(self):
        s = 'dchs'.upper()
        v = ' A 2 3 4 5 6 7 8 910 J Q K'
        return f'{v[self.value * 2:self.value * 2 + 2]}' \
            f'{s[self.suit]}{"^" if self.face_up else "v"}'

    def __eq__(self, other):
        # type: (Any) -> bool
        if isinstance(other, Card) and self.tup == other.tup:
            return True
        return False

    def __add__(self, other):
        # type: (Card) -> Tuple[bool, bool]
        if not isinstance(other, Card):
            raise ValueError('other must be of type Card')
        if other.blocked:
            return False, False
        tableau = False
        foundation = False
        if other.color != self.color and self.value - other.value == 1:
            tableau = True
        if other.color == self.color and self.value - other.value == -1:
            foundation = True
        return tableau, foundation


class History(object):
    def __init__(self):
        self.moves = []
        self.original_moves = {}

    def is_valid(self, card, start_parent, end_parent, start_area, end_area):
        # type: (Card, Union[Card, None], Union[Card, None], str, str) -> bool
        move = Move(card, start_parent, end_parent, start_area, end_area)
        if move in self.moves:
            return False
        return True

    def add(self, card, start_parent, end_parent, start_area, end_area):
        # type: (Card, Union[Card, None], Union[Card, None], str, str) -> bool
        move = Move(card, start_parent, end_parent, start_area, end_area)
        if move in self.moves:
            return False
        self.moves.append(move)
        return True


class Move(object):
    def __init__(self, card, start_parent, end_parent, start_area, end_area):
        # type: (Card, Union[Card, None], Union[Card, None], str, str) -> None
        sp_str = str(start_parent)
        ep_str = str(end_parent)
        self.move = str(card) + min(sp_str, ep_str) + max(sp_str, ep_str)
        self.move += start_area + end_area

    def __eq__(self, other):
        if not isinstance(other, Move):
            raise ValueError('can only compare to object of type Move')
        return self.move == other.move


if __name__ == '__main__':
    unsolved = True
    r = ReverseSolve(draw=1)
    while unsolved:
        try:
            r.solve()
        except RuntimeError:
            print('fail')
            r = ReverseSolve(draw=1, seed=r.r.getrandbits(2500))
        except KeyboardInterrupt:
            print('interrupted')
            break
        else:
            print('success')
            unsolved = False
    print(
        '\tdistances (t w f):',
        r.tableau.distance,
        r.waste.distance,
        r.foundation.distance,
        '\n\ttableau:',
        r.tableau.piles,
        '\n\ttableau_distances:',
        r.tableau.pile_distance,
        '\n\tfoundation:',
        r.foundation.piles,
        '\n\twaste:',
        r.waste.waste,
        '\n\tstack:',
        r.waste.stack
    )
