"""
Provide Tableau class.
"""

from typing import Optional

import card
from area import Area
from pile import Pile

__author__ = 'Tiziano Bettio'
__copyright__ = """
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
__license__ = 'MIT'
__version__ = '0.2'


class Tableau(Area):
    """
    Provides a tableau abstraction.
    """

    def __init__(self):
        super().__init__(TableauPile, 7)

    def move_pile(
            self,
            from_pile: int,
            num_cards: int,
            to_pile: Optional[int] = None
        ) -> int:
        """
        Try to move the top `num_cards` to an optionally specified pile.

        Args:
            from_pile: ``int`` -> the pile which to move cards away from.
            num_cards: ``int`` -> the amount of cards to move.
            to_pile: ``Optional[int]`` -> specify the destination

        Returns:
            The index of the pile it was moved to or -1 if no valid pile exists.
        """
        if from_pile == to_pile:
            raise ValueError('Expected from_pile and to_pile to be different.')
        if not self._piles[from_pile].pile:
            return -1
        piles = range(7) if to_pile is None else [to_pile]
        check_card = self._piles[from_pile][-num_cards]
        for pile in piles:
            if pile == from_pile:
                continue
            if self._piles[pile].valid(check_card):
                for n_card in self._piles[from_pile][-num_cards:]:
                    self._piles[pile].add(n_card)
                for _ in range(num_cards):
                    self._piles[from_pile].remove()
                return pile
        return -1

    def move_pile_force(
            self,
            from_pile: int,
            num_cards: int,
            to_pile: int
        ) -> int:
        """
        Force move the top `num_cards` to the specified pile.

        Args:
            from_pile: ``int`` -> the pile which to move cards away from.
            num_cards: ``int`` -> the amount of cards to move.
            to_pile: ``int`` -> specify the destination

        Returns:
            The index of the pile it was moved to or -1 if no valid pile exists.
        """
        if from_pile == to_pile:
            raise ValueError('Expected from_pile and to_pile to be different.')
        check_card = self._piles[from_pile][-num_cards]
        for n_card in self._piles[from_pile][-num_cards:]:
            self._piles[to_pile].add(n_card)
        for _ in range(num_cards):
            self._piles[from_pile].remove()

    def flip(self, pile: int) -> bool:
        """
        Flip the top most card of the specified pile.

        Returns:
            ``True`` if successful, otherwise ``False``.
        """
        top_card = self._piles[pile].top_card
        if top_card is not None and not top_card.visible:
            top_card.visible = True
            return True
        return False

    @property
    def issolved(self) -> bool:
        """
        If the tableau contains only face up cards.
        """
        for pile in self._piles:
            if not pile.issolved:
                return False
        return True


class TableauPile(Pile):
    """
    Provides a pile helper for the Tableau class.
    """

    def __init__(self, pos: int) -> None:
        super().__init__()
        self._pos = pos

    def valid(self, a_card: card.Card) -> bool:
        """
        Determine if adding the indicated card to this pile is valid.

        Args:
            a_card: :class:`card.Card` -> the card to verify.

        Returns:
            ``True`` if valid otherwise ``False``.
        """
        if self._pile:
            return self._pile[-1].tableau_valid(a_card)
        if a_card.value == 12:
            return True
        return False

    @property
    def isstart(self) -> bool:
        """
        If the pile is in its original state after a fresh deal.
        """
        if len(self._pile) != self._pos + 1:
            return False
        visible_count = 0
        hidden_count = 0
        for c_card in self._pile:
            if c_card.visible:
                visible_count += 1
            else:
                hidden_count += 1
        return hidden_count == self._pos and visible_count == 1

    @property
    def issolved(self) -> bool:
        """
        If the pile contains only face up cards.
        """
        if not self._pile:
            return True
        for c_card in self._pile:
            if not c_card.visible:
                return False
        return True
