"""
Provides the AABB class.
"""

from typing import List
from typing import Tuple
from typing import Union

from . import vector

__author__ = 'Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'
__copyright__ = """Copyright (c) 2019 Tiziano Bettio

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
SOFTWARE."""

POS_TYPE = Union[vector.Vector, vector.Point, Tuple[float, float], List[float]]
NUMERIC = Union[int, float]


class AABB(object):
    """
    Represents an Axis Aligned Bounding Box. Can be tested against
    with the overloaded operators (``<``, ``<=``, ``>=``, ``>``) as follows:

    >>> from engine.tools import vector
    >>>
    >>> a = AABB(box=(0.5, 0.5, 1.0, 1.0))
    >>> b = AABB(box=(0.5, 0.5, 0.7, 0.7))
    >>> a < b       # Is b completely inside a? (not touching)
    False
    >>> a <= b      # Is b inside a? (including exact overlap)
    True
    >>> a > b       # Is b overlapping a?
    True
    >>> a >= b      # Is b overlapping or touching a?
    True
    >>> a < vector.Point(0.75, 0.75)  # Is vector.Point at 0.75, 0.75 completely inside a?
    True

    :param box: ``4-Tuple[int/float]`` -> x1, y1, x2, y2 = top left and bottom
        right points of the bounding box.

    """
    def __init__(self, box):
        # type: (Tuple[NUMERIC, NUMERIC, NUMERIC, NUMERIC]) -> None
        if isinstance(box, tuple) and len(box) == 4 and \
                sum(
                    [1 if isinstance(i, (int, float)) else 0 for i in box]
                ) == 4:
            if box[0] < box[2] and box[1] < box[3]:
                self.box = box
            else:
                raise ValueError('invalid bounding box specified')
        else:
            raise TypeError('expected 4-Tuple[int/float]')

    def _test(self, other, test_type):
        # type: (Union[POS_TYPE, AABB], int) -> bool
        t = self.box
        if isinstance(other, AABB):
            o = other.box
            if test_type == 0:      # <=
                if t[0] <= o[0] and t[1] <= o[1] and t[2] >= o[2] \
                        and t[3] >= o[3]:
                    return True
            elif test_type == 1:    # <
                if t[0] < o[0] and t[1] < o[1] and t[2] > o[2] and t[3] > o[3]:
                    return True
            elif test_type == 2:    # >
                if t[0] < o[0] < t[2] and t[1] < o[1] < t[3]:
                    return True
                if t[0] < o[2] < t[2] and t[1] < o[3] < t[3]:
                    return True
                if other < self:
                    return True
            elif test_type == 3:    # >=
                if t[0] <= o[0] <= t[2] and t[1] <= o[1] <= t[3]:
                    return True
                if t[0] <= o[2] <= t[2] and t[1] <= o[3] <= t[3]:
                    return True
                if other <= self:
                    return True
            return False
        elif isinstance(other, vector.Point):
            p = other
        elif isinstance(other, (list, tuple)) and len(other) == 2:
            p = vector.Point(other)
        else:
            raise ValueError('Expected other to be of type AABB, vector.Point or '
                             'List/Tuple of length 2')
        if test_type in (0, 3):
            if t[0] <= p.x <= t[2] and t[1] <= p.y <= t[3]:
                return True
        else:
            if t[0] < p.x < t[2] and t[1] < p.y < t[3]:
                return True
        return False

    def inside(self, other, completely=False):
        # type: (Union[POS_TYPE, AABB], bool) -> bool
        """
        Test whether a box or point is inside this ``AABB``. This method yields
        the same results as using the ``<`` and ``<=`` operators would.

        :param other: ``AABB``, ``Vector/Point``, ``Iterable``
        :param completely: Optional ``bool`` -> whether ``other`` must lie
            entirely inside this ``AABB``.
        :return: ``bool``
        """
        if completely:
            return self._test(other, 0)
        return self._test(other, 1)

    def overlap(self, other, touching=True):
        # type: (Union[POS_TYPE, AABB], bool) -> bool
        """
        Test whether a box or point overlaps with this ``AABB``. This method
        yields the same results as using the ``>=`` and ``>`` operators would.

        :param other: ``AABB``, ``Vector/Point``, ``Iterable``
        :param touching: Optional ``bool`` -> whether to include the border of
            this ``AABB``.
        :return: ``bool``
        """
        if touching:
            return self._test(other, 3)
        return self._test(other, 2)

    def __le__(self, other):
        return self._test(other, 0)

    def __lt__(self, other):
        return self._test(other, 1)

    def __gt__(self, other):
        return self._test(other, 2)

    def __ge__(self, other):
        return self._test(other, 3)

    def __len__(self):
        return 4

    def __contains__(self, item):
        return True if item in range(4) else False

    def __getitem__(self, item):
        if item in range(4):
            return self.box[item]
        raise IndexError

    def __repr__(self):
        return f'{type(self).__name__}{self.__str__()}'

    def __str__(self):
        return str(self.box)
