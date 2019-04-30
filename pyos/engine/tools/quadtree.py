"""
Provides the Quadtree class and the helper class Children, together with a
convenience function to create a Quadtree instance from a list of pairs.
"""

from typing import Any
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from math import inf

from . import vector
from . import aabb

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
FLOAT4 = Tuple[float, float, float, float]


class Quadtree(object):
    """
    Simplistic QuadTree to store hashable objects in relation to their
    position indicated by either a Point, Tuple or an AABB instance.
    Objects can then be retrieved by position and removed by reference.

    .. warning::
        Any object reference stored in the QuadTree will not be garbage
        collected until the QuadTree goes out of scope. Any object stored should
        thus be removed with the appropriate call to ``QuadTree.remove(obj)``!

    Example Usage:

    >>> from engine.tools import aabb
    >>> from engine.tools import vector
    >>> q = Quadtree()
    >>> some_obj = tuple(range(10))
    >>> some_other_obj = tuple(reversed(range(10)))
    >>> some_aabb = aabb.AABB((0.1, 0.1, 0.2, 0.2))
    >>> some_point = vector.Point(0.7, 0.2)
    >>> q.add(some_obj, some_aabb)
    True
    >>> q.add(some_other_obj, some_point)
    True
    >>> q[aabb.AABB((0.11, 0.11, 0.19, 0.19))]
    [(0, 1, 2, 3, 4, 5, 6, 7, 8, 9)]
    >>> q[(aabb.AABB((-0.5, -0.5, 1.5, 1.5)), True)]
    [(0, 1, 2, 3, 4, 5, 6, 7, 8, 9), (9, 8, 7, 6, 5, 4, 3, 2, 1, 0)]

    """
    def __init__(self, box=(0.0, 0.0, 1.0, 1.0), max_level=8):
        # type: (FLOAT4, int) -> None
        self.aabb = aabb.AABB(box)
        self.children = Children(box)
        self.child_nodes = []       # type: List[Quadtree]
        self.items = []             # type: List[Any]
        self.positions = []         # type: List[Union[POS_TYPE, aabb.AABB]]
        self.max_level = max_level
        self.child_objects = {}

    @property
    def box(self):
        # type: () -> FLOAT4
        """``Tuple[float, float, float, float]``"""
        return self.aabb.box

    @property
    def item_count(self):
        # type: () -> int
        """``int``"""
        item_count = len(self.items)
        for child in self.child_nodes:
            item_count += child.item_count
        return item_count

    def get_items(self, pos, overlap=False):
        # type: (Union[POS_TYPE, aabb.AABB], Optional[bool]) -> List[Any]
        """
        Return all items that fulfill the ``AABB <= pos`` or ``AABB >= pos``
        condition
        """
        items = []
        pos_is_aabb = isinstance(pos, aabb.AABB)
        if self.aabb >= pos:    # potential matches
            for i, it in enumerate(self.items):
                it_pos = self.positions[i]
                it_pos_is_aabb = isinstance(it_pos, aabb.AABB)
                add = False
                if not pos_is_aabb and not it_pos_is_aabb:
                    a = vector.Point(tuple(pos))
                    b = vector.Point(tuple(it_pos))
                    if a.almost_equal(b):
                        add = True
                if not add and overlap:
                    if pos_is_aabb and pos >= it_pos:
                        add = True
                    elif not pos_is_aabb and it_pos_is_aabb and it_pos >= pos:
                        add = True
                elif not add and not overlap:
                    if pos_is_aabb and pos > it_pos:
                        add = True
                    elif not pos_is_aabb and it_pos_is_aabb and it_pos > pos:
                        add = True
                if add:
                    items.append(it)
            for child in self.child_nodes:
                items += child.get_items(pos, overlap)
        return items

    def add(self, obj, pos):
        # type: (Any, Union[POS_TYPE, aabb.AABB]) -> bool
        """Return ``True`` if successful, otherwise ``False``"""
        if self.aabb <= pos:
            if not self.max_level:
                self.items.append(obj)
                self.positions.append(pos)
                return True
            for i, child in enumerate(self.children):
                if child <= pos:
                    res = self.__add_to_child__(obj, pos, i)
                    if res:
                        self.child_objects[obj] = i
                    return res
            self.items.append(obj)
            self.positions.append(pos)
            return True
        return False

    def remove(self, obj):
        # type: (Any) -> bool
        """Return ``True`` if successful, otherwise ``False``"""
        if obj in self.items:
            index = self.items.index(obj)
            self.items.pop(index)
            self.positions.pop(index)
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
        # type: (Any, Union[POS_TYPE, aabb.AABB], int) -> bool
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
                return self.get_items(vector.Point(item))
            elif isinstance(item[0], (aabb.AABB, vector.Point, list, tuple)) \
                    and isinstance(item[1], bool):
                if isinstance(item[0], (tuple, list)) and \
                        len(item[0]) == 2 and \
                        isinstance(item[0][0], (int, float)) and \
                        isinstance(item[0][1], (int, float)):
                    p = vector.Point(tuple(item[0]))
                else:
                    p = item[0]
                return self.get_items(p, item[1])
        elif isinstance(item, (aabb.AABB, vector.Point, list, tuple)):
            return self.get_items(item)
        raise IndexError('index must be valid arguments to method get_items() '
                         'or an object reference that is stored in the '
                         'QuadTree')

    def __repr__(self):
        return f'{type(self).__name__}({self.__str__()})'

    def __str__(self):
        return f'({self.max_level}, {str(self.aabb)})[{self.item_count}]'


class Children(object):
    """
    Helper class for Quadtree to store the 4 child AABB of a node

    :param box: ``Tuple[float, float, float, float]`` -> the bounding box to be
        split in quarts.
    """
    def __init__(self, box):
        center = vector.Point(
            (box[2] - box[0]) / 2 + box[0],
            (box[3] - box[1]) / 2 + box[1]
        )
        self.ul = aabb.AABB(
            (
                box[0],
                box[1],
                center.x,
                center.y
            )
        )
        self.ur = aabb.AABB(
            (
                center.x,
                box[1],
                box[2],
                center.y
            )
        )
        self.dl = aabb.AABB(
            (
                box[0],
                center.y,
                center.x,
                box[3]
            )
        )
        self.dr = aabb.AABB(
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


def quadtree_from_pairs(quadtree_pairs, max_level=8):
    # type: (List[Tuple[aabb.AABB, Any]], Optional[int]) -> Union[Quadtree, None]
    """
    Returns an instance of Quadtree from a list of 2-tuple containing an AABB
    and object references to be stored in the quadtree. None is returned if
    either ``quadtree_pairs`` is empty or no valid bounds can be identified.

    :param quadtree_pairs: List -> (AABB, Any) pairs around which a quadtree
        should be built.
    :param max_level: Optional int -> maximum levels of nesting for the
        quadtree.
    """
    if not quadtree_pairs:
        return None
    x_min = y_min = inf
    x_max = y_max = -inf
    for pos_aabb, _ in quadtree_pairs:
        x_min = min(pos_aabb[0], pos_aabb[2], x_min)
        y_min = min(pos_aabb[1], pos_aabb[3], y_min)
        x_max = max(pos_aabb[0], pos_aabb[2], x_max)
        y_max = max(pos_aabb[1], pos_aabb[3], y_max)
    a = (x_max - x_min) * (y_max - y_min)
    if a in (0, inf, -inf):
        return None
    q = Quadtree((x_min, y_min, x_max, y_max), max_level)
    for pos_aabb, obj in quadtree_pairs:
        q.add(obj, pos_aabb)
    return q
