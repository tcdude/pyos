"""
Unittests for engine.taskmanager
"""

import math

import pytest

from engine import tools
from engine.tools import aabb
from engine.tools import quadtree

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


def test_vector_math():
    v_a = tools.Vector()
    v_b = tools.Vector(1.0, 1.0)
    assert v_a - v_b == tools.Vector(-1, -1)
    assert v_a + v_b * 2 == tools.Vector(2, 2)
    assert v_a + v_b / 2 == tools.Vector(0.5, 0.5)
    assert v_b // 3 == tools.Vector()
    assert 3 * v_b == tools.Vector(3, 3)
    assert 1 + v_a == tools.Vector(1, 1)
    assert 1 - v_b == tools.Vector()
    assert v_b.length == math.sqrt(2)
    assert pytest.approx(v_b.normalized().length) == 1
    assert v_b.rotate(90).almost_equal(tools.Vector(1, -1))
    assert v_b.rotate(-90).almost_equal(tools.Vector(-1, 1))
    with pytest.raises(ValueError) as e_info:
        v_a.normalize()
    assert 'zero length' in e_info.value.args[0]
    assert v_b.dot(v_b) == 2
    assert isinstance(v_a.aspoint(), tools.Point) is True


def test_aabb():
    b_a = aabb.AABB((0.0, 0.0, 1.0, 1.0))
    b_b = aabb.AABB((0.1, 0.1, 0.9, 0.9))
    b_c = aabb.AABB((0.1, 0.1, 1.0, 1.0))
    b_d = aabb.AABB((-0.5, -0.5, 0.5, 0.5))
    p_a = tools.Point(1.0, 1.0)
    p_b = tools.Point(1 - 1e-7, 1 - 1e-7)
    assert (b_a < b_b) is True
    assert (b_a < b_c) is False
    assert (b_a <= b_c) is True
    assert (b_a <= p_a) is True
    assert (b_a < p_a) is False
    assert (b_a > b_d) is True
    assert (b_a > p_a) is False
    assert (b_a >= p_a) is True
    assert (b_a > p_b) is True


def test_quadtree():
    qt = quadtree.Quadtree((-1.0, -1.0, 1.0, 1.0), 16)
    pos_a = aabb.AABB((0.0, 0.0, 1.0, 1.0))
    pos_b = aabb.AABB((0.1, 0.1, 1.9, 1.9))
    pos_c = aabb.AABB((-1.1, -1.1, 0.0, 0.0))
    pos_d = aabb.AABB((-0.5, -0.5, 0.5, 0.5))
    pos_e = tools.Point(0.45, 0.45)
    obj_a = (0, 0)
    obj_b = (1, 1)
    obj_c = (2, 2)
    obj_d = (3, 3)
    obj_e = (4, 4)
    assert qt.add(obj_a, pos_a) is True
    assert qt.add(obj_b, pos_b) is False
    assert qt.add(obj_c, pos_c) is False
    assert qt.add(obj_d, pos_d) is True
    assert qt.add(obj_e, pos_e) is True
    assert qt.item_count == 3
    result = qt[pos_d]
    assert len(result) == 2
    assert obj_e in result
    result = qt[aabb.AABB((-1.0, -1.0, 0.0, 0.0))]
    assert len(result) == 1
    assert obj_d in result
    result = qt[aabb.AABB((-1.0, -1.0, 0.0, 0.0)), True]
    assert len(result) == 2
    assert obj_a in result


def test_quadtree_from_pairs():
    pairs = [
        (
            aabb.AABB((0.0, 0.0, 1.0, 1.0)),
            (0, 0)
        ),
        (
            aabb.AABB((0.1, 0.1, 1.9, 1.9)),
            (1, 1)
        ),
        (
            aabb.AABB((-1.1, -1.1, 0.0, 0.0)),
            (2, 2)
        ),
        (
            aabb.AABB((-0.5, -0.5, 0.5, 0.5)),
            (3, 3)
        ),
    ]
    qt = quadtree.quadtree_from_pairs(pairs, 16)
    assert qt.add((4, 4), tools.Point(0.45, 0.45)) is True
    assert qt.aabb.box == (-1.1, -1.1, 1.9, 1.9)
    assert qt.item_count == 5
    result = qt[aabb.AABB((-1.0, -1.0, 0.0, 0.0))]
    assert len(result) == 1
    assert (3, 3) in result
    result = qt[aabb.AABB((-1.0, -1.0, 0.0, 0.0)), True]
    assert len(result) == 3
    assert (0, 0) in result
