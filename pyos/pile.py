"""
Provide Tableau class.
"""

from typing import List
from typing import Union
import abc

import card

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


class Pile:
    """
    Representation of a pile of cards.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, unused_pos=None) -> None:
        self._pile: List[card.Card] = []

    def add(self, a_card: card.Card) -> None:
        """
        Adds the card to this pile, w/o determining validity of the move.

        Args:
            a_card: :class:`card.Card` -> the card to add.
        """
        self._pile.append(a_card)

    def remove(self) -> None:
        """
        Remove the top most card of the pile.
        """
        self._pile.pop()

    @abc.abstractmethod
    def valid(self, a_card: card.Card) -> bool:
        """
        To be overridden by the subclass.

        Args:
            a_card: :class:`card.Card` -> the card to verify.

        Returns:
            ``True`` if valid otherwise ``False``.
        """
        return False

    @property
    @abc.abstractmethod
    def isstart(self) -> bool:
        """
        To be overridden by the subclass.
        """
        return False

    @property
    def top_card(self) -> Union[None, card.Card]:
        """
        Top most card of the pile, or ``None`` if the pile is empty.
        """
        if self._pile:
            return self._pile[-1]
        return None

    @property
    def pile(self) -> List[card.Card]:
        """
        The entire pile.
        """
        return self._pile

    def __getitem__(self, item):
        return self._pile[item]
