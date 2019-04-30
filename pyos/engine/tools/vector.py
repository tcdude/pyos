"""
Provides 2D Vector and Point classes.
"""
from typing import Optional
from typing import Tuple
from typing import Union
import math

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

NUMERIC = Union[int, float]


class Vector(object):
    """
    2D Vector type.

    :param x: Optional ``int/float`` or ``Tuple[int/float, int/float]`` ->
        either x value or tuple of x and y.
    :param y: Optional ``int/float`` -> y value, is ignored when a tuple is
        passed in for ``x``.
    :param d: Optional ``float`` -> delta used in the ``__eq__`` comparison of
        two Vector objects. Defaults to ``1e-6`` to avoid errors due to
        floating point precision.
    """
    def __init__(
            self,
            x=0,    # type: Optional[Union[NUMERIC, Tuple[NUMERIC, NUMERIC]]]
            y=0,    # type: Optional[NUMERIC]
            d=1e-6  # type: Optional[float]
    ):
        # type: (...) -> None
        if isinstance(x, tuple):
            if len(x) == 2:
                x, y = x
            else:
                raise TypeError('expected tuple of length 2')
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise TypeError('numerical types expected for x and y')
        self._x = x
        self._y = y
        self._d = d
        self._changed = True
        self._length = None
        self._rtype = Vector

    def __repr__(self):
        return f'{type(self).__name__}({self._x:.4f}, {self._y:.4f})'

    def __str__(self):
        return self.__repr__()

    @property
    def x(self):
        # type: () -> NUMERIC
        """``x`` value"""
        return self._x

    @property
    def y(self):
        # type: () -> NUMERIC
        """``y`` value"""
        return self._y

    @x.setter
    def x(self, v):
        # type: (NUMERIC) -> None
        if isinstance(v, (int, float)):
            self._x = v
            self._changed = True
        else:
            raise TypeError('Must be of type int or float')

    @y.setter
    def y(self, v):
        # type: (NUMERIC) -> None
        if isinstance(v, (int, float)):
            self._y = v
            self._changed = True
        else:
            raise TypeError('Must be of type int or float')

    @property
    def length(self):
        # type: () -> float
        """``length`` of the vector"""
        if self._changed:
            self._length = math.sqrt(self.x ** 2 + self.y ** 2)
            self._changed = False
        return self._length

    def normalized(self):
        # type: () -> Vector
        """Returns a normalized Vector of this Vector instance."""
        vlen = self.length
        if vlen:
            return Vector(self.x / vlen, self.y / vlen)
        raise ValueError('Vector of zero length cannot be normalized')

    def normalize(self):
        # type: () -> bool
        """
        Normalizes the Vector and returns True if successful. Raises a
        ValueError if the Vector is of zero length.
        """
        vlen = self.length
        if vlen:
            self._changed = True
            self._x /= vlen
            self._y /= vlen
            return True
        raise ValueError('Vector of zero length cannot be normalized')

    def rotate(self, degrees):
        # type: (NUMERIC) -> Vector
        """
        Returns a Vector rotated ``degrees`` around the origin.

        :param degrees: int/float -> angle of rotation in degrees.
        """
        a = math.radians(-degrees)
        sa = math.sin(a)
        ca = math.cos(a)
        return Vector(ca * self.x - sa * self.y, sa * self.x + ca * self.y)

    def dot(self, other):
        # type: (Vector) -> float
        """
        Returns the dot product of ``this`` ⋅ ``other``

        :param other: Vector -> the other Vector for the dot product.
        """
        if isinstance(other, Vector):
            return self.x * other.x + self.y * other.y

    def asint(self, rounding=False):
        # type: (Optional[bool]) -> Vector
        """
        Returns the Vector with its values cast to int. If rounding is True,
        rounds the value first, before casting (default=False).

        :param rounding: Optional bool -> Whether to round the values first.
        """
        if rounding:
            return self._rtype(int(round(self.x, 0)), int(round(self.y, 0)))
        return self._rtype(int(self.x), int(self.y))

    def aspoint(self):
        # type: () -> Point
        """Returns the current Vector as Point."""
        return Point(*self)

    def almost_equal(self, other, d=1e-6):
        # type: (Union[Vector, Point], Optional[float]) -> bool
        """Returns ``True`` if difference is less than or equal to ``d``."""
        if isinstance(other, Vector):
            d = abs(d)
            return abs(self.x - other.x) <= d and abs(self.y - other.y) <= d
        raise TypeError('expected type Vector or Point')

    def __getitem__(self, key):
        # type: (Union[int, str]) -> NUMERIC
        if key in (0, 'x'):
            return self.x
        if key in (1, 'y'):
            return self.y
        raise IndexError('Invalid Index for Vector2 object')

    def __len__(self):
        # type: () -> int
        return 2

    def __add__(self, other):
        # type: (Union[Vector, int, float, Tuple[NUMERIC, NUMERIC]]) -> Vector
        if isinstance(other, (int, float)):
            return self._rtype(self.x + other, self.y + other)
        elif isinstance(other, Vector):
            return self._rtype(self.x + other.x, self.y + other.y)
        elif isinstance(other, tuple) and len(other) == 2 and \
                isinstance(other[0], (int, float)) and \
                isinstance(other[1], (int, float)):
            return self._rtype(self.x + other[0], self.y + other[1])
        else:
            raise TypeError('Must be of type Vector, int or float')

    def __radd__(self, other):
        # type: (Union[Vector, int, float, Tuple[NUMERIC, NUMERIC]]) -> Vector
        return self.__add__(other)

    def __sub__(self, other):
        # type: (Union[Vector, int, float, Tuple[NUMERIC, NUMERIC]]) -> Vector
        if isinstance(other, (int, float)):
            return self._rtype(self.x - other, self.y - other)
        elif isinstance(other, Vector):
            return self._rtype(self.x - other.x, self.y - other.y)
        elif isinstance(other, tuple) and len(other) == 2 and \
                isinstance(other[0], (int, float)) and \
                isinstance(other[1], (int, float)):
            return self._rtype(self.x - other[0], self.y - other[1])
        else:
            raise TypeError('Must be of type Vector, int or float')

    def __rsub__(self, other):
        # type: (Union[Vector, int, float, Tuple[NUMERIC, NUMERIC]]) -> Vector
        if isinstance(other, (int, float)):
            return self._rtype(other - self.x, other - self.y)
        elif isinstance(other, Vector):
            return self._rtype(other.x - self.x, other.y - self.y)
        elif isinstance(other, tuple) and len(other) == 2 and \
                isinstance(other[0], (int, float)) and \
                isinstance(other[1], (int, float)):
            return self._rtype(other[0] - self.x, other[1] - self.y)
        else:
            raise TypeError('Must be of type Vector, int or float')

    def __mul__(self, other):
        # type: (NUMERIC) -> Vector
        if isinstance(other, (int, float)):
            return self._rtype(self.x * other, self.y * other)
        else:
            raise TypeError('Must be of type int or float')

    def __rmul__(self, other):
        # type: (NUMERIC) -> Vector
        return self.__mul__(other)

    def __truediv__(self, other):
        # type: (NUMERIC) -> Vector
        if isinstance(other, (int, float)):
            return self._rtype(self.x / other, self.y / other)
        else:
            raise TypeError('Must be of type int or float')

    def __floordiv__(self, other):
        # type: (NUMERIC) -> Vector
        if isinstance(other, (int, float)):
            return self._rtype(self.x // other, self.y // other)
        else:
            raise TypeError('Must be of type int or float')

    def __eq__(self, other):
        # type: (Vector) -> bool
        return self.almost_equal(other, self._d)


class Point(Vector):
    def __init__(self, x=0, y=0):
        # type: (Union[NUMERIC, Tuple], NUMERIC) -> None
        super(Point, self).__init__(x, y)
        self._rtype = Point
