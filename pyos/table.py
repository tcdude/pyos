"""
Provides the Table class that handles game state.
"""

from dataclasses import dataclass
import pickle
import time
from typing import Callable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from loguru import logger

import card
import common
import foundation
import rules
import tableau

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



@dataclass
class TableRepresentation:
    """Typed class of the table representation."""
    stack: List[card.Card]
    waste: List[card.Card]
    tableau: List[List[card.Card]]
    foundation: List[List[card.Card]]


@dataclass
class Move:
    """Typed class to hold move information."""
    from_area: common.TableArea
    from_pile_id: Optional[int] = -1
    pile_count: Optional[int] = 1
    to_area: Optional[common.TableArea] = None
    to_pile_id: Optional[int] = -1


@dataclass
class State:
    """Typed class to hold state information."""
    # pylint: disable=too-many-instance-attributes
    start_time: float = 0.0
    elapsed_time: float = 0.0
    last_move: float = 0.0
    moves: int = 0
    points: int = 0
    paused: bool = True
    fresh_deal: bool = False
    seed: Union[None, int] = None
    draw_count: int = 1
    result: Union[None, Tuple[float, int, int, int]] = None


class Table:
    """
    Provides handling of the game state.
    """
    # pylint: disable=too-many-public-methods,too-many-instance-attributes
    def __init__(
            self,
            callback: Callable[
                [card.Card, common.TableLocation, List[int]], None]
        ) -> None:
        self._tableau = tableau.Tableau()
        self._foundation = foundation.Foundation()
        self._stack: List[card.Card] = []
        self._waste: List[card.Card] = []
        self._history: List[Move] = []
        self._state = State()
        self._callback = callback
        self._shuffler = rules.Shuffler()
        self._wrapped = {
            'draw': self.__wrap_method(self.__draw),
            'flip': self.__wrap_method(self.__flip),
            'undo': self.__wrap_method(self.__undo),
            'w2t': self.__wrap_method(self.__waste_to_tableau),
            'w2f': self.__wrap_method(self.__waste_to_foundation),
            't2f': self.__wrap_method(self.__tableau_to_foundation),
            't2t': self.__wrap_method(self.__tableau_to_tableau),
            'f2t': self.__wrap_method(self.__foundation_to_tableau)
        }

    @property
    def draw(self) -> Callable:
        """Method for drawing a card from the Stack."""
        return self._wrapped['draw']

    @property
    def flip(self) -> Callable:
        """Method to flip a card face up on the Tableau."""
        return self._wrapped['flip']

    @property
    def undo(self) -> Callable:
        """Method to undo the last move."""
        return self._wrapped['undo']

    @property
    def waste_to_tableau(self) -> Callable:
        """Method to move a card from the Waste to the Tableau."""
        return self._wrapped['w2t']

    @property
    def waste_to_foundation(self) -> Callable:
        """Method to move a card from the Waste to the Foundation."""
        return self._wrapped['w2f']

    @property
    def tableau_to_foundation(self) -> Callable:
        """Method to move a card from the Tableau to the Foundation."""
        return self._wrapped['t2f']

    @property
    def tableau_to_tableau(self) -> Callable:
        """Method to move a card from the Tableau to the Tableau."""
        return self._wrapped['t2t']

    @property
    def foundation_to_tableau(self) -> Callable:
        """Method to move a card from the Foundation to the Tableau."""
        return self._wrapped['f2t']

    @property
    def draw_count(self) -> int:
        """Draw count (1 or 3)."""
        return self._state.draw_count

    @draw_count.setter
    def draw_count(self, value: int) -> None:
        if value not in (1, 3):
            raise ValueError('only values 1 or 3 are allowed')
        self._state.draw_count = value

    @property
    def waste_card(self) -> Union[card.Card, None]:
        """The top most card on the waste pile."""
        return self._waste[-1] if self._waste else None

    @property
    def stats(self) -> Tuple[int, float, int]:
        """Returns the current moves, time and points."""
        g_time = 0.0
        if not self._state.paused and not self._state.fresh_deal:
            g_time = time.perf_counter() - self._state.start_time
        elif self._state.paused and not self._state.fresh_deal:
            g_time = self._state.elapsed_time
        return self._state.moves, g_time, self._state.points

    @property
    def result(self) -> Tuple[float, int, int, int]:
        """
        Available when win_condition is True.

        Returns:
            Tuple of time, points, bonus and moves.
        """
        if not self.win_condition:
            raise ValueError('only available when win_condition is True')
        if self._state.result is None:
            elapsed_time = self._state.last_move - self._state.start_time
            bonus = rules.bonus(elapsed_time)
            self._state.result = (
                elapsed_time,
                self._state.points,
                bonus,
                self._state.moves
            )
        return self._state.result

    @property
    def win_condition(self) -> bool:
        """Whether the win condition is met."""
        return self._foundation.isfinished

    @property
    def is_paused(self) -> bool:
        """Whether the game is currently paused."""
        return self._state.paused

    @property
    def solved(self) -> bool:
        """Whether all cards on the tableau are face up."""
        return self._tableau.issolved

    @property
    def table(self) -> TableRepresentation:
        """Current TableRepresentation."""
        return TableRepresentation(
            stack=self._stack,
            waste=self._waste,
            tableau=self._tableau.piles,
            foundation=self._foundation.piles
        )

    @property
    def shuffler(self) -> rules.Shuffler:
        """The shuffler."""
        return self._shuffler

    def deal(
            self,
            random_seed: Optional[int] = None,
            win_deal: Optional[bool] = True
        ) -> None:
        """
        New deal.

        Args:
            random_seed: Optional[int] unsigned in range 2^31.
            win_deal: Optional[bool] whether winner deal is enabled.
        """
        if win_deal:
            res = self._shuffler.winner_deal(random_seed, self.draw_count)
        else:
            res = self._shuffler.deal(random_seed)
        self._state.seed = res[0]
        logger.debug(f'Random Seed: {self._state.seed}')
        self._tableau.reset()
        for pile_pos, pile in enumerate(res[1]):
            for (suit, value), visible in pile:
                p_card = card.Card(suit, value)
                if visible:
                    p_card.visible = True
                self._tableau.add_card_force(p_card, pile_pos)
        self._stack = [card.Card(suit, value) for suit, value in res[2]]
        self._waste = []
        self._foundation.reset()
        self._state.paused = True
        self._state.fresh_deal = True
        self._state.points = 0
        self._state.moves = 0
        self._state.result = None
        self._history = []

    def _start(self) -> None:
        """To be called when a game starts."""
        if self._state.fresh_deal:
            logger.info('First move of the game')
            self._state.start_time = time.perf_counter()
            self._state.moves = 0
            self._state.paused = False
            self._state.fresh_deal = False

    def pause(self) -> None:
        """Pause the game."""
        if self._state.paused:
            return
        logger.info('Pausing game')
        self._state.elapsed_time = self.stats[1]
        self._state.paused = True

    def _resume(self) -> None:
        """Resume the game."""
        if not self._state.paused:
            return
        new_start = time.perf_counter() - self._state.elapsed_time
        logger.info(f'Resuming game old time = {self._state.start_time}, '
                    f'new start time = {new_start}, elapsed time = '
                    f'{self._state.elapsed_time}')
        self._state.start_time = new_start
        self._state.paused = False

    def reset(self) -> None:
        """Reset the game to its start position."""
        logger.info('Reset table')
        self.deal(self._state.seed)

    def _increment_moves(self) -> None:
        """Increment moves by 1."""
        self._state.moves += 1
        self._state.last_move = time.perf_counter()

    def get_state(self, pause: Optional[bool] = True) -> bytes:
        """
        Retrieve current game state and optionally pause the game.

        Args:
            pause: Optional[bool] whether to also pause the game.
                (default=True).

        Returns:
            bytes -> output of pickle.dumps
        """
        logger.debug('Retrieving state')
        if pause:
            self.pause()
        return pickle.dumps(
            (
                self._stack,
                self._waste,
                self._foundation,
                self._tableau,
                self._state,
                self._history
            )
        )

    def set_state(self, state: bytes) -> None:
        """
        Set a stored game state.

        Args:
            state: bytes -> an output from pickle.dumps
        """
        try:
            (
                self._stack,
                self._waste,
                self._foundation,
                self._tableau,
                self._state,
                self._history
            ) = pickle.loads(state)
            logger.info('State set')
        except pickle.UnpicklingError:
            logger.warning('Invalid state')
        self._state.paused = True

    def refresh_table(self):
        """
        Execute callback for every card on the table.
        """
        for i, t_card in enumerate(self._stack):
            self._callback(
                t_card,
                common.TableLocation(
                    area=common.TableArea.STACK,
                    visible=False,
                    card_id=i
                )
            )
        for i, t_card in enumerate(self._waste):
            pile_id = min(len(self._waste) - i - 1, 3)
            self._callback(
                t_card,
                common.TableLocation(
                    area=common.TableArea.WASTE,
                    visible=True,
                    pile_id=pile_id,
                    card_id=i
                )
            )
        for i, pile in enumerate(self._tableau.piles):
            for j, t_card in enumerate(pile):
                self._callback(
                    t_card,
                    common.TableLocation(
                        area=common.TableArea.TABLEAU,
                        visible=t_card.visible,
                        pile_id=i,
                        card_id=j
                    )
                )
        for i, pile in enumerate(self._foundation.piles):
            for j, t_card in enumerate(pile):
                self._callback(
                    t_card,
                    common.TableLocation(
                        area=common.TableArea.FOUNDATION,
                        visible=True,
                        pile_id=i,
                        card_id=j
                    )
                )

    def __wrap_method(self, meth: Callable) -> Callable:
        """
        Method wrapper for triggered and move counted methods.

        Args:
            meth: the method to be wrapped.

        Returns:
            Callable.
        """
        def wrapper(*args, **kwargs):
            res = meth(*args, **kwargs)
            if res:
                if self._state.fresh_deal:
                    self._start()
                elif self._state.paused:
                    self._resume()
                logger.info(f'{meth.__name__} returned valid move. Moves +1')
                self._increment_moves()
            return res
        return wrapper

    def __flip(self, pile: int) -> bool:
        """
        Tries to flip the top most card of the specified pile.

        Args:
            pile: pile index.

        Returns:
            True if a move is performed otherwise False.
        """
        res = self._tableau.flip(pile)
        if res:
            self._history.append(
                Move(
                    from_area=common.TableArea.TABLEAU,
                    from_pile_id=pile,
                    pile_count=1,
                    to_area=common.TableArea.TABLEAU,
                    to_pile_id=pile
                )
            )
            self._callback(
                self._tableau.top_card(pile),
                common.TableLocation(
                    area=common.TableArea.TABLEAU,
                    visible=True,
                    pile_id=pile,
                    card_id=len(self._tableau.piles[pile]) - 1
                )
            )
        return False

    def __waste_to_tableau(self, pile: Optional[int] = None) -> bool:
        """
        Tries to move a card from Waste to Tableau.

        Args:
            pile: pile index.

        Returns:
            True if a move is performed otherwise False.
        """
        w_card = self.waste_card
        if w_card is None:
            logger.debug('no waste card')
            return False
        dest_pile = self._tableau.add_card(w_card, pile)
        if dest_pile < 0:
            logger.debug('no valid move found')
            return False
        logger.debug('valid move found')
        self._history.append(
            Move(
                from_area=common.TableArea.WASTE,
                from_pile_id=-1,
                pile_count=1,
                to_area=common.TableArea.TABLEAU,
                to_pile_id=dest_pile
            )
        )
        self._waste.pop()
        self._state.points += 5
        self._update_tableau_pile(dest_pile)
        self._reset_waste()
        return True

    def __waste_to_foundation(self, pile: Optional[int] = None) -> bool:
        """
        Tries to move a card from Waste to Foundation.

        Args:
            pile: pile index.

        Returns:
            True if a move is performed otherwise False.
        """
        w_card = self.waste_card
        if w_card is None:
            logger.debug('no waste card')
            return False
        dest_pile = self._foundation.add_card(w_card, pile)
        if dest_pile < 0:
            logger.debug('no valid move found')
            return False
        logger.debug('valid move found')
        self._history.append(
            Move(
                from_area=common.TableArea.WASTE,
                from_pile_id=-1,
                pile_count=1,
                to_area=common.TableArea.FOUNDATION,
                to_pile_id=dest_pile
            )
        )
        self._waste.pop()
        self._state.points += 10
        self._callback(
            self._foundation.top_card(dest_pile),
            common.TableLocation(
                area=common.TableArea.FOUNDATION,
                visible=True,
                pile_id=dest_pile,
                card_id=len(self._foundation.piles[dest_pile]) - 1
            )
        )
        self._reset_waste()
        return True

    def __tableau_to_foundation(
            self,
            tableau_pile: Optional[int] = None,
            foundation_pile: Optional[int] = None
        ) -> bool:
        """
        Tries to move a card from Tableau to Foundation.

        Args:
            tableau_pile: pile index on Tableau.
            foundation_pile: pile index on Foundation.

        Returns:
            True if a move is performed otherwise False.
        """
        if tableau_pile is None:
            test_cards = [(i, self._tableau.top_card(i)) for i in range(7)]
        else:
            test_cards = [(tableau_pile, self._tableau.top_card(tableau_pile))]
        for from_pile, t_card in test_cards:
            if t_card is None:
                continue
            dest_pile = self._foundation.add_card(t_card, foundation_pile)
            if dest_pile > -1:
                self._history.append(
                    Move(
                        from_area=common.TableArea.TABLEAU,
                        from_pile_id=from_pile,
                        pile_count=1,
                        to_area=common.TableArea.FOUNDATION,
                        to_pile_id=dest_pile
                    )
                )
                self._tableau.remove(from_pile)
                logger.debug('valid move found')
                self._state.points += 10
                self._callback(
                    self._foundation.top_card(dest_pile),
                    common.TableLocation(
                        area=common.TableArea.FOUNDATION,
                        visible=True,
                        pile_id=dest_pile,
                        card_id=len(self._foundation.piles[dest_pile]) - 1
                    )
                )
                self._update_tableau_pile(from_pile)
                return True
        logger.debug('no valid move found')
        return False

    def __tableau_to_tableau(
            self,
            from_pile: Optional[int] = None,
            to_pile: Optional[int] = None,
            num_cards: Optional[int] = 1
        ) -> bool:
        """
        Try to perform a tableau to tableau move.

        Args:
            from_pile: pile index.
            to_pile: pile index.
            num_cards: number of cards.

        Returns:
            True if a move is performed otherwise False.
        """
        from_piles = range(7) if from_pile is None else [from_pile]
        for pile in from_piles:
            if pile == to_pile:
                continue
            dest_pile = self._tableau.move_pile(pile, num_cards, to_pile)
            if dest_pile > -1:
                self._history.append(
                    Move(
                        from_area=common.TableArea.TABLEAU,
                        from_pile_id=pile,
                        pile_count=num_cards,
                        to_area=common.TableArea.TABLEAU,
                        to_pile_id=dest_pile
                    )
                )
                self._update_tableau_pile(dest_pile)
                self._update_tableau_pile(pile)
                return True
        return False

    def __foundation_to_tableau(
            self,
            foundation_pile: int,
            tableau_pile: Optional[int] = None
        ) -> bool:
        """
        Tries to move a card from Foundation to Tableau.

        Args:
            foundation_pile: pile index on Foundation.
            tableau_pile: pile index on Tableau.

        Returns:
            True if a move is performed otherwise False.
        """
        f_card = self._foundation.top_card(foundation_pile)
        if f_card is None:
            return False
        dest_pile = self._tableau.add_card(f_card, tableau_pile)
        if dest_pile > -1:
            self._history.append(
                Move(
                    from_area=common.TableArea.FOUNDATION,
                    from_pile_id=foundation_pile,
                    pile_count=1,
                    to_area=common.TableArea.TABLEAU,
                    to_pile_id=dest_pile
                )
            )
            self._foundation.remove(foundation_pile)
            logger.debug('valid move found')
            self._state.points = max(0, self._state.points - 15)
            self._update_tableau_pile(dest_pile)
            return True
        logger.debug('no valid move found')
        return False

    def __draw(self) -> Union[bool, int]:
        """
        Try to draw from stack.

        Returns:
            Union[bool, int] -> 1 = draw, 2 = reset stack, False = empty.
        """
        if not self._stack:
            if not self._waste:
                logger.debug('no more cards')
                return False
            self._stack = list(reversed(self._waste))
            self._waste = []
            for i, s_card in enumerate(self._stack):
                s_card.visible = False
                self._callback(
                    s_card,
                    common.TableLocation(
                        area=common.TableArea.STACK,
                        visible=False,
                        card_id=i
                    )
                )
            self._state.points -= 100 if self._state.draw_count == 1 else 0
            self._state.points = max(self._state.points, 0)
            logger.info('reset stack')
            self._history.append(
                Move(
                    from_area=common.TableArea.WASTE,
                    to_area=common.TableArea.STACK
                )
            )
            self._state.points -= 100 if self.draw_count == 1 else 0
            self._state.points = max(0, self._state.points)
            return 2
        card_count = min(self._state.draw_count, len(self._stack))
        for _ in range(self._state.draw_count):
            if self._stack:
                self._waste.append(self._stack.pop())
                self._waste[-1].visible = True
            else:
                break
        self._history.append(
            Move(
                from_area=common.TableArea.STACK,
                to_area=common.TableArea.WASTE,
                pile_count=card_count
            )
        )
        self._reset_waste()
        logger.info('draw successful')
        return 1

    def __undo(self) -> bool:
        """
        Try to undo the last move.

        Returns:
            bool -> True if successful otherwise False.
        """
        if not self._history:
            logger.warning('history is empty')
            return False
        move = self._history.pop()

        success = False
        if move.from_area == common.TableArea.STACK:
            success = self.__undo_draw(move)
        elif move.from_area == common.TableArea.WASTE:
            success = self.__undo_waste_to(move)
        elif move.from_area == common.TableArea.TABLEAU:
            success = self.__undo_tableau_to(move)
        elif move.from_area == common.TableArea.FOUNDATION and \
              move.to_area == common.TableArea.TABLEAU:
            success = self.__undo_foundation_to(move)

        if not success:
            raise RuntimeError(f'Illegal move ({repr(move)}) to undo.')
        self._state.points = max(0, self._state.points - 15)
        return True

    def __undo_draw(self, move: Move) -> bool:
        """
        Undo a draw operation.

        Args:
            move: Move

        Returns:
            bool -> True if successful otherwise False.
        """
        for _ in range(move.pile_count):
            w_card = self._waste.pop()
            w_card.visible = False
            self._stack.append(w_card)
            self._callback(
                w_card,
                common.TableLocation(
                    area=common.TableArea.STACK,
                    visible=False,
                    card_id=len(self._stack) - 1
                )
            )
        self._reset_waste()
        return True

    def __undo_waste_to(self, move: Move) -> bool:
        """
        Undo a Waste to ... operation.

        Args:
            move: Move

        Returns:
            bool -> True if successful otherwise False.
        """
        if move.to_area == common.TableArea.TABLEAU:
            w_card = self._tableau.top_card(move.to_pile_id)
            self._waste.append(w_card)
            self._tableau.remove(move.to_pile_id)
            self._update_tableau_pile(move.to_pile_id)
        elif move.to_area == common.TableArea.FOUNDATION:
            w_card = self._foundation.top_card(move.to_pile_id)
            self._waste.append(w_card)
            self._foundation.remove(move.to_pile_id)
        elif move.to_area == common.TableArea.STACK:
            self._waste = list(reversed(self._stack))
            self._stack = []
            w_len = len(self._waste)
            for i, w_card in enumerate(self._waste):
                pile_id = min(3, w_len - i - 1)
                w_card.visible = True
                self._callback(
                    w_card,
                    common.TableLocation(
                        area=common.TableArea.WASTE,
                        visible=True,
                        pile_id=pile_id,
                        card_id=i
                    )
                )
        else:
            return False
        self._reset_waste()
        return True

    def __undo_tableau_to(self, move: Move) -> bool:
        """
        Undo a Tableau to ... operation.

        Args:
            move: Move

        Returns:
            bool -> True if successful otherwise False.
        """
        if move.to_area == common.TableArea.TABLEAU and \
                move.from_pile_id != move.to_pile_id:
            self._tableau.move_pile_force(
                move.to_pile_id,
                move.pile_count,
                move.from_pile_id
            )
            self._update_tableau_pile(move.to_pile_id)
            self._update_tableau_pile(move.from_pile_id)
        elif move.to_area == common.TableArea.TABLEAU and \
                move.from_pile_id == move.to_pile_id:
            self._tableau.top_card(move.from_pile_id).visible = False
            self._callback(
                self._tableau.top_card(move.from_pile_id),
                common.TableLocation(
                    area=common.TableArea.TABLEAU,
                    visible=False,
                    pile_id=move.from_pile_id,
                    card_id=len(self._tableau.piles[move.from_pile_id]) - 1
                )
            )
            move = self._history.pop()
            self.__undo_tableau_to(move)
        elif move.to_area == common.TableArea.FOUNDATION:
            t_card = self._foundation.top_card(move.to_pile_id)
            self._tableau.add_card_force(t_card, move.from_pile_id)
            self._foundation.remove(move.to_pile_id)
            self._update_tableau_pile(move.from_pile_id)
        else:
            return False
        return True

    def __undo_foundation_to(self, move: Move) -> bool:
        """
        Undo a Foundation to Tableau operation.

        Args:
            move: Move

        Returns:
            bool -> True if successful otherwise False.
        """
        f_card = self._tableau.top_card(move.to_pile_id)
        self._foundation.add_card_force(f_card, move.from_pile_id)
        self._tableau.remove(move.to_pile_id)
        self._callback(
            self._foundation.top_card(move.from_pile_id),
            common.TableLocation(
                area=common.TableArea.FOUNDATION,
                visible=True,
                pile_id=move.from_pile_id,
                card_id=len(self._foundation.piles[move.from_pile_id]) - 1
            )
        )
        self._update_tableau_pile(move.to_pile_id)
        return True

    def _reset_waste(self) -> None:
        """Make sure all waste card callbacks are executed."""
        w_len = len(self._waste)
        for i in range(min(5, w_len)):
            card_id = w_len - i - 1
            self._callback(
                self._waste[card_id],
                common.TableLocation(
                    area=common.TableArea.WASTE,
                    visible=True,
                    pile_id=min(i, 3),
                    card_id=card_id
                )
            )

    def _update_tableau_pile(self, pile_id: int) -> None:
        """Make sure all cards in a tableau pile get updated."""
        for i, t_card in enumerate(self._tableau.piles[pile_id]):
            self._callback(
                t_card,
                common.TableLocation(
                    area=common.TableArea.TABLEAU,
                    visible=t_card.visible,
                    pile_id=pile_id,
                    card_id=i
                )
            )
