"""
Cython implementation of Vector and Point classes.
"""

from libc.math cimport sin
from libc.math cimport cos
from libc.math cimport sqrt
from libc.math cimport pi


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


cdef inline double radians(degrees):
    return (degrees / 180.0) * pi


cdef class Vector:
    def __init__(self, x=0, y=0, precision=1e-6):
        if isinstance(x, tuple):
            if len(x) == 2:
                x, y = x
            else:
                raise TypeError('expected tuple of length 2')
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise TypeError('numerical types expected for x and y')
        self._x = x
        self._y = y
        self._precision = precision
        self._length = 0.0
        self._dirty = 1
        self._rtype = Vector

    def __repr__(self):
        return f'{type(self).__name__}{str(self)}'

    def __str__(self):
        return str((self._x, self._y))

    @property
    def x(self):
        """``x`` value"""
        return self._x

    @property
    def y(self):
        """``y`` value"""
        return self._y

    @x.setter
    def x(self, v):
        if isinstance(v, (int, float)):
            self._x = v
            self._dirty = 1
        else:
            raise TypeError('Must be of type int or float')

    @y.setter
    def y(self, v):
        if isinstance(v, (int, float)):
            self._y = v
            self._dirty = 1
        else:
            raise TypeError('Must be of type int or float')

    @property
    def rtype(self):
        return self._rtype

    @property
    def length(self):
        # type: () -> float
        """``length`` of the vector"""
        if self._dirty:
            self._length = sqrt(self.x ** 2 + self.y ** 2)
            self._dirty = 0
        return self._length

    cpdef Vector normalized(self):
        """Returns a normalized Vector of this Vector instance."""
        vlen = self.length
        if vlen:
            return Vector(self.x / vlen, self.y / vlen)
        raise ValueError('Vector of zero length cannot be normalized')

    cpdef normalize(self):
        """
        Normalizes the Vector and returns True if successful. Raises a
        ValueError if the Vector is of zero length.
        """
        vlen = self.length
        if vlen:
            self._dirty = 1
            self._x /= vlen
            self._y /= vlen
            return True
        raise ValueError('Vector of zero length cannot be normalized')

    cpdef Vector rotate(self, degrees):
        """
        Returns a Vector rotated ``degrees`` around the origin.

        :param degrees: int/float -> angle of rotation in degrees.
        """
        a = radians(-degrees)
        sa = sin(a)
        ca = cos(a)
        return Vector(ca * self.x - sa * self.y, sa * self.x + ca * self.y)

    cpdef dot(self, Vector other):
        """
        Returns the dot product of ``this`` ⋅ ``other``

        :param other: Vector -> the other Vector for the dot product.
        """
        if isinstance(other, Vector):
            return self.x * other.x + self.y * other.y

    cpdef Vector asint(self, int rounding=0):
        """
        Returns the Vector with its values cast to int. If rounding is True,
        rounds the value first, before casting (default=False).

        :param rounding: Optional bool -> Whether to round the values first.
        """
        if rounding:
            return self._rtype(int(round(self.x, 0)), int(round(self.y, 0)))
        return self._rtype(int(self.x), int(self.y))

    cpdef Point aspoint(self):
        # type: () -> Point
        """Returns the current Vector as Point."""
        return Point(*self)

    cpdef bint almost_equal(self, other, double d=1e-6):
        """Returns ``True`` if difference is less than or equal to ``d``."""
        if isinstance(other, Vector):
            d = abs(d)
            return abs(self.x - other.x) <= d and abs(self.y - other.y) <= d
        raise TypeError('expected type Vector or Point')

    def __getitem__(self, key):
        if key in (0, 'x'):
            return self.x
        if key in (1, 'y'):
            return self.y
        raise IndexError('Invalid Index for Vector2 object')

    def __len__(self):
        return 2

    def __add__(self, other):
        if isinstance(self, Vector) and isinstance(other, (int, float)):
            return self.rtype(self.x + other, self.y + other)
        elif isinstance(self, Vector) and isinstance(other, Vector):
            return self.rtype(self.x + other.x, self.y + other.y)
        elif isinstance(other, Vector) and isinstance(self, (int, float)):
            return other.rtype(other.x + self, other.y + self)
        elif isinstance(other, tuple) and len(other) == 2 and \
                isinstance(other[0], (int, float)) and \
                isinstance(other[1], (int, float)) and isinstance(self, Vector):
            return self.rtype(self.x + other[0], self.y + other[1])
        elif isinstance(self, tuple) and len(self) == 2 and \
                isinstance(self[0], (int, float)) and \
                isinstance(self[1], (int, float)) and isinstance(other, Vector):
            return other.rtype(other.x + self[0], other.y + self[1])
        else:
            raise TypeError('Must be of type Vector, tuple, int or float')

    def __sub__(self, other):
        if isinstance(self, Vector) and isinstance(other, Vector):
            return self.rtype(self.x - other.x, self.y - other.y)
        elif isinstance(self, Vector) and isinstance(other, (int, float)):
            return self.rtype(self.x - other, self.y - other)
        elif isinstance(other, Vector) and isinstance(self, (int, float)):
            return other.rtype(self - other.x, self - other.y)
        elif isinstance(other, tuple) and len(other) == 2 and \
                isinstance(other[0], (int, float)) and \
                isinstance(other[1], (int, float)) and isinstance(self, Vector):
            return self.rtype(self.x - other[0], self.y - other[1])
        elif isinstance(self, tuple) and len(self) == 2 and \
                isinstance(self[0], (int, float)) and \
                isinstance(self[1], (int, float)) and isinstance(other, Vector):
            return other.rtype(self[0] - other.x, self[1] - other.y)
        else:
            raise TypeError('Must be of type Vector, tuple, int or float')

    def __mul__(self, other):
        if isinstance(self, Vector) and isinstance(other, (int, float)):
            return self.rtype(self.x * other, self.y * other)
        elif isinstance(self, (int, float)) and isinstance(other, Vector):
            return other.rtype(self * other.x, self * other.y)
        else:
            raise TypeError('Must be of type int or float')

    def __truediv__(self, other):
        if isinstance(self, Vector) and isinstance(other, (int, float)):
            return self.rtype(self.x / other, self.y / other)
        elif isinstance(self, (int, float)) and isinstance(other, Vector):
            return other.rtype(self / other.x, self / other.y)
        else:
            raise TypeError('Must be of type int or float')

    def __floordiv__(self, other):
        if isinstance(self, Vector) and isinstance(other, (int, float)):
            return self.rtype(self.x // other, self.y // other)
        elif isinstance(self, (int, float)) and isinstance(other, Vector):
            return other.rtype(self // other.x, self // other.y)
        else:
            raise TypeError('Must be of type int or float')

    def __eq__(self, other):
        return self.almost_equal(other, self._precision)


cdef class Point(Vector):
    def __init__(self, x=0, y=0):
        Vector.__init__(self, x, y)
        self._rtype = Point
