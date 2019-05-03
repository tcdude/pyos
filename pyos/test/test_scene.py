"""
Unittests for engine.taskmanager
"""
import pytest

from engine.scene import layout
from engine.scene import node
from engine.scene import nodepath
from engine.scene import viewport
from engine import tools
from engine.tools import aabb

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


def create_empty_np():
    np = nodepath.NodePath()
    np.asset_pixel_ratio = 720
    np.set_dummy_size((1.0, 1.0))
    np.traverse()
    return np


def test_nodepath_relative_position():
    np = create_empty_np()
    assert np.relative_position == tools.Point()
    np.center = tools.BOTTOM_RIGHT
    assert np.dirty is True
    assert np.traverse() is True
    assert np.relative_position == tools.Point(-1.0, -1.0)
    np.center = tools.CENTER
    assert np.dirty is True
    assert np.traverse() is True
    assert np.relative_position == tools.Point(-0.5, -0.5)


def test_nodepath_nesting():
    np = create_empty_np()
    child = np
    for i in range(1000):
        child = child.attach_new_node_path(f'Child{i:03d}')
        child.position = 0.1, 0.1
        child.set_dummy_size((1.0, 1.0))
    assert np.traverse() is True
    assert child.relative_position == tools.Point(100.0, 100.0)
    np.angle = 90
    assert np.traverse() is True
    assert child.relative_position == tools.Point(100.0, -100.0)


def test_nodepath_query():
    np = create_empty_np()
    c = np.attach_new_node_path('Child')
    c.set_dummy_size((0.25, 0.25))
    c.position = 0.8, 0.8
    assert np.dirty is True
    assert np.traverse() is True
    assert len(np.query(aabb.AABB((0, 0, 1, 1)))) == 2
    result = np.query(aabb.AABB((1.01, 1.01, 1.1, 1.1)))
    assert len(result) == 1
    assert c in result
    result = np.query(aabb.AABB((0, 0, 0.2, 0.2)))
    assert len(result) == 1
    assert np in result


def test_nodepath_dirty():
    np = create_empty_np()
    c = np.attach_new_node_path('Child')
    c.set_dummy_size((0.25, 0.25))
    c.position = 0.8, 0.8
    assert np.traverse() is True
    np.dirty = True
    assert c.dirty is True


def test_nodepath_dict():
    np = create_empty_np()
    np['test'] = (1, 1)
    assert np['test'] == (1, 1)
    assert 'test' in np
    assert np.pop('test') == (1, 1)
    assert 'test' not in np


def test_grid_layout():
    np = create_empty_np()
    grid = layout.GridLayout(
        np,
        (0.0, 0.0, 1.0, 1.5),
        rows=[5],
        cols=[10, 20, None, 20, None]
    )
    assert np.traverse() is True
    assert grid[1, 1].size == pytest.approx((0.2, 0.3))
    assert grid[1, 2].size == pytest.approx((0.25, 0.3))
    assert grid[1, 1].relative_position == tools.Point(0.1, 0.3)
    assert grid[1, 2].relative_position == tools.Point(0.3, 0.3)
    assert grid[3, 3].relative_position == tools.Point(0.55, 0.9)


def test_grid_layout_margins():
    np = create_empty_np()
    with pytest.raises(ValueError) as e_info:
        _ = layout.GridLayout(
            np,
            (0.0, 0.0, 1.0, 1.5),
            rows=[5],
            cols=[10, 20, None, 20, None],
            margins=(0.05, 0.05)
        )
    assert e_info.match(r'.*margins are equal or larger.*')
    np = create_empty_np()
    grid = layout.GridLayout(
        np,
        (0.0, 0.0, 1.0, 1.5),
        rows=[5],
        cols=[10, 20, None, 20, None],
        margins=(0.01, 0.01)
    )
    assert np.traverse() is True
    assert grid[1, 1].size == pytest.approx((0.18, 0.28))
    assert grid[1, 2].size == pytest.approx((0.23, 0.28))
    assert grid[1, 1].relative_position == tools.Point(0.11, 0.31)
    assert grid[1, 2].relative_position == tools.Point(0.31, 0.31)
    assert grid[3, 3].relative_position == tools.Point(0.56, 0.91)
