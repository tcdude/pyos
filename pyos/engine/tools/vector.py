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
import math

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'


class Vector(object):
    def __init__(self, x=0, y=0):
        # type: (Union[int, float], Union[int, float]) -> None
        self.__x__ = x
        self.__y__ = y
        self.__changed__ = True
        self.__length__ = None
        self.__rtype__ = Vector

    def __repr__(self):
        return f'{type(self).__name__}({self.__x__:.4f}, {self.__y__:.4f})'

    def __str__(self):
        return self.__repr__()

    @property
    def x(self):
        return self.__x__

    @property
    def y(self):
        return self.__y__

    @x.setter
    def x(self, v):
        if isinstance(v, (int, float)):
            self.__x__ = v
            self.__changed__ = True
        else:
            raise TypeError('Must be of type int or float')

    @y.setter
    def y(self, v):
        if isinstance(v, (int, float)):
            self.__y__ = v
            self.__changed__ = True
        else:
            raise TypeError('Must be of type int or float')

    @property
    def length(self):
        if self.__changed__:
            self.__length__ = math.sqrt(self.x ** 2 + self.y ** 2)
            self.__changed__ = False
        return self.__length__

    def normalized(self):
        vlen = self.length
        if vlen:
            return Vector(self.x / vlen, self.y / vlen)
        raise ValueError('Vector of zero length cannot be normalized')

    def normalize(self):
        vlen = self.length
        if vlen:
            self.__changed__ = True
            self.__x__ /= vlen
            self.__y__ /= vlen
            return True
        raise ValueError('Vector of zero length cannot be normalized')

    def dot(self, other):
        if isinstance(other, Vector):
            return self.x * other.x + self.y * other.y

    def asint(self, rounding=False):
        if rounding:
            return self.__rtype__(int(round(self.x, 0)), int(round(self.y, 0)))
        return self.__rtype__(int(self.x), int(self.y))

    def __getitem__(self, key):
        if key in (0, 'x'):
            return self.x
        if key in (1, 'y'):
            return self.y
        raise IndexError('Invalid Index for Vector2 object')

    def __add__(self, other):
        if isinstance(other, (int, float)):
            return self.__rtype__(self.x + other, self.y + other)
        elif isinstance(other, Vector):
            return self.__rtype__(self.x + other.x, self.y + other.y)
        else:
            raise TypeError('Must be of type Vector2, int or float')

    def __sub__(self, other):
        if isinstance(other, (int, float)):
            return self.__rtype__(self.x - other, self.y - other)
        elif isinstance(other, Vector):
            return self.__rtype__(self.x - other.x, self.y - other.y)
        else:
            raise TypeError('Must be of type Vector2, int or float')

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return self.__rtype__(self.x * other, self.y * other)
        else:
            raise TypeError('Must be of type int or float')

    def __rmul__(self, other):
        if isinstance(other, (int, float)):
            return self.__rtype__(self.x * other, self.y * other)
        else:
            raise TypeError('Must be of type int or float')

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return self.__rtype__(self.x / other, self.y / other)
        else:
            raise TypeError('Must be of type int or float')

    def __floordiv__(self, other):
        if isinstance(other, (int, float)):
            return self.__rtype__(self.x // other, self.y // other)
        else:
            raise TypeError('Must be of type int or float')

    def __eq__(self, other):
        if isinstance(other, Vector):
            if self.x == other.x and self.y == other.y:
                return True
        return False


class Point(Vector):
    def __init__(self, x=0, y=0):
        # type: (Union[int, float], Union[int, float]) -> None
        super(Point, self).__init__(x, y)
        self.__rtype__ = Point
