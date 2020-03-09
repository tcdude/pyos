"""
Area abstract base class.
"""

import abc
from typing import List
from typing import Optional
from typing import Type
from typing import Union

import card
from pile import Pile

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


class Area:
    """
    Provides a area abstraction.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, pile_type: Type[Pile], num_piles: int):
        self._pile_type = pile_type
        self._num_piles = num_piles
        self._piles: List[Type[Pile]] = [pile_type(i) for i in range(num_piles)]

    def reset(self):
        """Reset area piles."""
        self._piles = [self._pile_type(i) for i in range(self._num_piles)]

    def add_card_force(self, a_card: card.Card, pos: int):
        """
        Add a card to the area to the specified pile

        Args:
            a_card: :class:`card.Card` -> the card to be added to the area.
            pos: ``int`` -> destination pile.
        """
        self._piles[pos].add(a_card)

    def add_card(self, a_card: card.Card, pos: Optional[int] = None) -> int:
        """
        Try to add a card to the area from another area, optionally
        specifying the pile.

        Args:
            a_card: :class:`card.Card` -> the card to be added to the area.
            pos: ``Optional[int]`` -> if specified, the card will only be tried
                to be added to the indicated pile.

        Returns:
            The index of the pile it was added to or -1 if no valid pile exists.
        """
        piles = range(self._num_piles) if pos is None else [pos]
        for pile in piles:
            if self._piles[pile].valid(a_card):
                self._piles[pile].add(a_card)
                return pile
        return -1

    def remove(self, pile: int) -> None:
        """
        Removes the top most card of the specified pile.
        """
        self._piles[pile].remove()

    def top_card(self, pile: int) -> Union[None, card.Card]:
        """
        Return the top most card
        """
        return self._piles[pile].top_card

    @property
    def isstart(self) -> bool:
        """
        If the area is in its original state after a fresh deal.
        """
        for pile in self._piles:
            if not pile.isstart:
                return False
        return True

    @property
    def piles(self) -> List[List[card.Card]]:
        """
        All piles from the area.
        """
        return [pile.pile for pile in self._piles]
