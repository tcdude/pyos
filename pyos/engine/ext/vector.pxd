"""
Cython implementation of Vector and Point classes.
"""

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


cdef class Vector:
    cdef _x, _y
    cdef double _precision, _length
    cdef int _dirty
    cdef object _rtype

    cpdef Vector normalized(self)
    cpdef normalize(self)
    cpdef Vector rotate(self, degrees)
    cpdef dot(self, Vector other)
    cpdef Vector asint(self, int rounding=*)
    cpdef Point aspoint(self)
    cpdef bint almost_equal(self, other, double d=*)


cdef class Point(Vector):
    pass
