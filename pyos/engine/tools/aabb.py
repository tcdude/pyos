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
from typing import Union

from engine.tools.quadtree import POS_TYPE
from engine.tools.vector import Point

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'


class AABB(object):
    """
        Represents an Axis Aligned Bounding Box. Can be tested against
        with the overloaded operators (<, <=, >=, >) as follows:

        >>> from engine.tools.aabb import AABB
        >>> from engine.tools.vector import Point
        >>>
        >>> a = AABB(box=(0.5, 0.5, 1.0, 1.0))
        >>> b = AABB(box=(0.5, 0.5, 0.7, 0.7))
        >>> a < b       # Is b completely inside a? (not touching)
        ... False
        >>> a <= b      # Is b inside a? (including exact overlap)
        ... True
        >>> a > b       # Is b overlapping a?
        ... True
        >>> a >= b      # Is b overlapping or touching a?
        ... True
        >>> a < Point(0.75, 0.75)  # Is Point at 0.75, 0.75 completely inside a?
        ... True
        """
    def __init__(self, box):
        self.box = box

    def __test__(self, other, test_type):
        # type: (Union[POS_TYPE, AABB], int) -> bool
        t = self.box
        if isinstance(other, AABB):
            o = other.box
            if test_type == 0:
                if t[0] <= o[0] and t[1] <= o[1] and t[2] >= o[2] \
                        and t[3] >= o[3]:
                    return True
            elif test_type == 1:
                if t[0] < o[0] and t[1] < o[1] and t[2] > o[2] and t[3] > o[3]:
                    return True
            elif test_type == 2:
                if t[0] < o[0] < t[2] and t[1] < o[1] < t[3]:
                    return True
                if t[0] < o[2] < t[2] and t[1] < o[3] < t[3]:
                    return True
                if other < self:
                    return True
            elif test_type == 3:
                if t[0] <= o[0] <= t[2] and t[1] <= o[1] <= t[3]:
                    return True
                if t[0] <= o[2] <= t[2] and t[1] <= o[3] <= t[3]:
                    return True
                if other <= self:
                    return True
            return False
        elif isinstance(other, Point):
            p = other
        elif isinstance(other, (list, tuple)) and len(other) == 2:
            p = Point(*other)
        else:
            raise ValueError('Expected other to be of type AABB, Point or '
                             'List/Tuple of length 2')
        if test_type in (0, 2, 3):
            if t[0] <= p.x <= t[2] and t[1] <= p.y <= t[3]:
                return True
        elif test_type == 1:
            if t[0] < p.x < t[2] and t[1] < p.y < t[3]:
                return True
        return False

    def __le__(self, other):
        return self.__test__(other, 0)

    def __lt__(self, other):
        return self.__test__(other, 1)

    def __gt__(self, other):
        return self.__test__(other, 2)

    def __ge__(self, other):
        return self.__test__(other, 3)

    def __len__(self):
        return 4

    def __getitem__(self, item):
        if isinstance(item, int) and -1 < item < 4:
            return self.box[item]
        raise IndexError

    def __repr__(self):
        return f'AABB({", ".join([str(i) for i in self.box])})'

    def __str__(self):
        return self.__repr__()