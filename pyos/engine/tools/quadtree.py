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

from typing import Any
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from math import inf

from engine.tools import Vector
from engine.tools.aabb import AABB
from engine.tools.vector import Point

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'

POS_TYPE = Union[Vector, Point, Tuple[float, float], List[float]]
FLOAT4 = Tuple[float, float, float, float]


class Quadtree(object):
    """
    Simplistic QuadTree to store hashable objects in relation to their
    position indicated by either a Point, Tuple or an AABB instance.
    Objects can then be retrieved by position and removed by reference.
    Warning! Any object reference stored in the QuadTree will not be garbage
    collected until the QuadTree goes out of scope. Any object stored should
    thus be removed with the appropriate call to `QuadTree.remove(obj)`!

    Example Usage:
    >>> q = Quadtree()
    >>> some_obj = tuple(range(10))
    >>> some_other_obj = tuple(reversed(range(10)))
    >>> some_aabb = AABB((0.1, 0.1, 0.2, 0.2))
    >>> some_point = Point(0.7, 0.2)
    >>> q.add(some_obj, some_aabb)
    ... True
    >>> q.add(some_other_obj, some_point)
    ... True
    >>> q[AABB((0.11, 0.11, 0.19, 0.19))]
    ... [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]
    >>> q[(AABB((-0.5, -0.5, 1.5, 1.5)), True)]
    ... [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]]
    """
    def __init__(self, box=(0.0, 0.0, 1.0, 1.0), max_level=8):
        # type: (FLOAT4, int) -> None
        self.aabb = AABB(box)
        self.children = Children(box)
        self.child_nodes = []  # type: List[Quadtree]
        self.items = []  # type: List[Any]
        self.max_level = max_level
        self.child_objects = {}

    @property
    def box(self):
        return self.aabb.box

    @property
    def item_count(self):
        item_count = len(self.items)
        for child in self.child_nodes:
            item_count += child.item_count
        return item_count

    def get_items(self, pos, overlap=False):
        # type: (Union[POS_TYPE, AABB], Optional[bool]) -> List[Any]
        """
        Return all items that fulfill the `AABB <= pos` or `AABB >= pos`
        condition
        """
        if not overlap and self.aabb <= pos:
            items = self.items[:]
            for child in self.child_nodes:
                items += child.get_items(pos, overlap)
            return items
        elif overlap and self.aabb >= pos:
            items = self.items[:]
            for child in self.child_nodes:
                items += child.get_items(pos, overlap)
            return items
        return []

    def add(self, obj, pos):
        # type: (Any, Union[POS_TYPE, AABB]) -> bool
        """Return True if successful, otherwise False"""
        if self.aabb <= pos:
            if not self.max_level:
                self.items.append(obj)
                return True
            for i, child in enumerate(self.children):
                if child <= pos:
                    res = self.__add_to_child__(obj, pos, i)
                    if res:
                        self.child_objects[obj] = i
                    return res
            self.items.append(obj)
            return True
        return False

    def remove(self, obj):
        # type: (Any) -> bool
        """Return True if successful, otherwise False"""
        if obj in self.items:
            self.items.pop(self.items.index(obj))
            return True
        if obj in self.child_objects:
            if self.child_nodes[self.child_objects[obj]].remove(obj):
                self.__prune__()
                return True
        return False

    def __prune__(self):
        """Remove empty branches"""
        if not sum([c.item_count for c in self.child_nodes]):
            self.child_nodes = []
        else:
            for child in self.child_nodes:
                child.__prune__()

    def __add_to_child__(self, obj, pos, i):
        # type: (Any, Union[POS_TYPE, AABB], int) -> bool
        """Internal method to control nesting"""
        if not self.child_nodes:
            if not self.max_level:
                return False
            for child in self.children:
                self.child_nodes.append(Quadtree(child.box, self.max_level - 1))
        return self.child_nodes[i].add(obj, pos)

    def __getitem__(self, item):
        if item in self.child_objects:
            return self.child_nodes[self.child_objects[item]][item]
        elif item in self.items:
            return [item]
        elif isinstance(item, (tuple, list)) and len(item) == 2:
            if isinstance(item[0], (int, float)) and \
                    isinstance(item[1], (int, float)):
                return self.get_items(Point(*item))
            elif isinstance(item[0], (AABB, Point, list, tuple)) and \
                    isinstance(item[1], bool):
                return self.get_items(*item)
        elif isinstance(item, (AABB, Point, list, tuple)):
            return self.get_items(item)
        raise IndexError('index must be valid arguments to method get_items() '
                         'or an object reference that is stored in the '
                         'QuadTree')

    def __repr__(self):
        return f'{type(self).__name__}({str(self.aabb)}) / Level ' \
               f'{self.max_level}'

    def __str__(self):
        return self.__repr__()


class Children(object):
    """Helper class for QuadTree to store the 4 child AABB of a node"""
    def __init__(self, box):
        center = Point(
            (box[2] - box[0]) / 2 + box[0],
            (box[3] - box[1]) / 2 + box[1]
        )
        self.ul = AABB(
            (
                box[0],
                box[1],
                center.x,
                center.y
            )
        )
        self.ur = AABB(
            (
                center.x,
                box[1],
                box[2],
                center.y
            )
        )
        self.dl = AABB(
            (
                box[0],
                center.y,
                center.x,
                box[3]
            )
        )
        self.dr = AABB(
            (
                center.x,
                center.y,
                box[2],
                box[3]
            )
        )

    def __getitem__(self, item):
        if isinstance(item, (int, str)):
            if item in (0, 'ul'):
                return self.ul
            elif item in (1, 'ur'):
                return self.ur
            elif item in (2, 'dl'):
                return self.dl
            elif item in (3, 'dr'):
                return self.dr
        raise IndexError(f'no such item "{str(item)}"')

    def __repr__(self):
        return f'{type(self).__name__}({", ".join([str(i) for i in self])})'

    def __str__(self):
        return self.__repr__()


def quadtree_from_pairs(quad_tree_pairs, max_level=8):
    # type: (List[Tuple[AABB, Any]], Optional[int]) -> Union[Quadtree, None]
    if not quad_tree_pairs:
        return
    x_min, y_min = inf
    x_max, y_max = -inf
    for aabb, _ in quad_tree_pairs:
        x_min = min(aabb[0], aabb[2], x_min)
        y_min = min(aabb[1], aabb[3], y_min)
        x_max = max(aabb[0], aabb[2], x_max)
        y_max = max(aabb[1], aabb[3], y_max)
    a = (x_max - x_min) * (y_max - y_min)
    if a in (0, inf, -inf):
        return None
    q = Quadtree((x_min, y_min, x_max, y_max), max_level)
    for aabb, obj in quad_tree_pairs:
        q.add(obj, aabb)
    return q
