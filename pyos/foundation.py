"""
Provide Foundation class.
"""

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


class Foundation(Area):
    """
    Provide an abstraction of the foundation.
    """

    def __init__(self):
        super().__init__(FoundationPile, 4)

    @property
    def isfinished(self) -> bool:
        """
        If the foundation is in the winning state.
        """
        for pile in self._piles:
            if len(pile.pile) != 13:
                return False
        return True


class FoundationPile(Pile):
    """
    Provides a pile helper for the Foundation class.
    """

    def valid(self, a_card: card.Card) -> bool:
        """
        Determine if adding the indicated card to this pile is valid.

        Args:
            a_card: :class:`card.Card` -> the card to verify.

        Returns:
            ``True`` if valid otherwise ``False``.
        """
        if self._pile:
            return self._pile[-1].foundation_valid(a_card)
        if a_card.value == 0:
            return True
        return False

    @property
    def isstart(self) -> bool:
        """
        If the pile is in its original state after a fresh deal.
        """
        return len(self._pile) == 0
