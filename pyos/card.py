"""
Provide Card class.
"""

import common

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


class Card:
    """
    Representation of a card. Provides `*_valid` methods to check for valid
    moves.

    Args:
        suit: ``int`` -> value from 0 to 3.
    """

    def __init__(self, suit: int, value: int) -> None:
        self._suit = suit
        self._value = value
        self._visible = False

    @property
    def suit(self) -> int:
        """
        Suit of the card.
        """
        return self._suit

    @property
    def value(self) -> int:
        """
        Value of the card.
        """
        return self._value

    @property
    def visible(self) -> bool:
        """
        Whether the card is visible.
        """
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError
        self._visible = value

    @property
    def image(self) -> str:
        """
        Returns the image path for the current representation (e.g. the path to
        the specific card if visible otherwise the path to the card back).
        """
        if self._visible:
            return f'images/{common.COLORS[self.suit]}' \
                   f'{common.DENOMINATIONS[self.value]}.png'
        return common.CARDBACK

    @property
    def index(self) -> int:
        """
        Returns an index helper to map a Card to a corresponding ImageNode.
        """
        return (self._suit, self._value), 0 if self._visible else 1

    def tableau_valid(self, other: 'Card') -> bool:
        """
        Check if the `other` card is allowed to be placed on top of this card.

        Args:
            other: :class:`Card` -> the card to be checked against.
        """
        if not self._visible:
            return False
        if self._suit % 2 != other.suit % 2 and other.value == self._value - 1:
            return True
        return False

    def foundation_valid(self, other: 'Card') -> bool:
        """
        Check if appending the specified card is a valid tableau move.

        Args:
            other: :class:`Card` -> the card to be appended.
        """
        if self.suit == other.suit and other.value == self.value + 1:
            return True
        return False

    def __eq__(self, other: 'Card') -> bool:
        return self._suit == other.suit and self._value == other.value and \
            self._visible == other.visible

    def __neq__(self, other: 'Card') -> bool:
        return not self.__eq__(other)

    def __repr__(self):
        return f'Card({common.DENOMINATIONS[self.value].upper()} ' \
               f'{common.COLORS[self.suit].upper()} ' \
               f'{"v" if self._visible else "h"})'

    def __str__(self):
        return self.__repr__()
