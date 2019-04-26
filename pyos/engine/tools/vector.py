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

    :param x: Optional (int, 2-tuple) -> either x value or tuple of x and y
    :param y: Optional int -> y value, is ignored when a tuple is passed in for
        ``x``.
    """
    def __init__(self, x=0, y=0):
        # type: (Union[NUMERIC, Tuple], NUMERIC) -> None
        if isinstance(x, tuple):
            if len(x) == 2:
                x, y = x
            else:
                raise TypeError('expected tuple of length 2')
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise TypeError('numerical types expected for x and y')
        self.__x = x
        self.__y = y
        self.__changed = True
        self.__length = None
        self.__rtype__ = Vector

    def __repr__(self):
        return f'{type(self).__name__}({self.__x:.4f}, {self.__y:.4f})'

    def __str__(self):
        return self.__repr__()

    @property
    def x(self):
        # type: () -> NUMERIC
        """``x`` value"""
        return self.__x

    @property
    def y(self):
        # type: () -> NUMERIC
        """``y`` value"""
        return self.__y

    @x.setter
    def x(self, v):
        # type: (NUMERIC) -> None
        if isinstance(v, (int, float)):
            self.__x = v
            self.__changed = True
        else:
            raise TypeError('Must be of type int or float')

    @y.setter
    def y(self, v):
        # type: (NUMERIC) -> None
        if isinstance(v, (int, float)):
            self.__y = v
            self.__changed = True
        else:
            raise TypeError('Must be of type int or float')

    @property
    def length(self):
        # type: () -> float
        """``length`` of the vector"""
        if self.__changed:
            self.__length = math.sqrt(self.x ** 2 + self.y ** 2)
            self.__changed = False
        return self.__length

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
            self.__changed = True
            self.__x /= vlen
            self.__y /= vlen
            return True
        raise ValueError('Vector of zero length cannot be normalized')

    def rotate(self, degrees):
        # type: (NUMERIC) -> Vector
        """
        Returns a Vector rotated ``degrees`` around the origin.

        :param degrees: int/float -> angle of rotation in degrees.
        """
        a = math.radians(degrees)
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
            return self.__rtype__(int(round(self.x, 0)), int(round(self.y, 0)))
        return self.__rtype__(int(self.x), int(self.y))

    def aspoint(self):
        # type: () -> Point
        """Returns the current Vector as Point."""
        return Point(*self)

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
        # type: (Union[Vector, int, float]) -> Vector
        if isinstance(other, (int, float)):
            return self.__rtype__(self.x + other, self.y + other)
        elif isinstance(other, Vector):
            return self.__rtype__(self.x + other.x, self.y + other.y)
        else:
            raise TypeError('Must be of type Vector, int or float')

    def __sub__(self, other):
        # type: (Union[Vector, int, float]) -> Vector
        if isinstance(other, (int, float)):
            return self.__rtype__(self.x - other, self.y - other)
        elif isinstance(other, Vector):
            return self.__rtype__(self.x - other.x, self.y - other.y)
        else:
            raise TypeError('Must be of type Vector, int or float')

    def __mul__(self, other):
        # type: (NUMERIC) -> Vector
        if isinstance(other, (int, float)):
            return self.__rtype__(self.x * other, self.y * other)
        else:
            raise TypeError('Must be of type int or float')

    def __rmul__(self, other):
        # type: (NUMERIC) -> Vector
        if isinstance(other, (int, float)):
            return self.__rtype__(self.x * other, self.y * other)
        else:
            raise TypeError('Must be of type int or float')

    def __truediv__(self, other):
        # type: (NUMERIC) -> Vector
        if isinstance(other, (int, float)):
            return self.__rtype__(self.x / other, self.y / other)
        else:
            raise TypeError('Must be of type int or float')

    def __floordiv__(self, other):
        # type: (NUMERIC) -> Vector
        if isinstance(other, (int, float)):
            return self.__rtype__(self.x // other, self.y // other)
        else:
            raise TypeError('Must be of type int or float')

    def __eq__(self, other):
        # type: (Vector) -> Vector
        if isinstance(other, Vector):
            if self.x == other.x and self.y == other.y:
                return True
        return False


class Point(Vector):
    def __init__(self, x=0, y=0):
        # type: (NUMERIC, NUMERIC) -> None
        super(Point, self).__init__(x, y)
        self.__rtype__ = Point
