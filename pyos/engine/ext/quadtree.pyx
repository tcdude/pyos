"""
Cython implementation of Quadtree class.
"""

from math import inf

from .vector cimport Point
from .aabb cimport AABB

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

cdef class Quadtree:
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
    def __cinit__(self, box=(0.0, 0.0, 1.0, 1.0), max_level=8):
        self.aabb = AABB(box)
        self.children = Children(box)
        self.child_nodes = []
        self.items = []
        self.positions = []
        self.max_level = max_level

    @property
    def box(self):
        """``Tuple[float, float, float, float]``"""
        return self.aabb.box

    @property
    def item_count(self):
        """``int``"""
        item_count = len(self.items)
        for child in self.child_nodes:
            item_count += child.item_count
        return item_count

    # noinspection PyUnresolvedReferences
    cpdef list get_items(self, pos, bint overlap=False):
        """
        Return all items that fulfill the ``AABB <= pos`` or ``AABB >= pos``
        condition
        """
        cdef list potential_items = []
        cdef list positions = []
        cdef bint pos_is_aabb = isinstance(pos, AABB)
        cdef list potential_matches = [self]
        cdef long i
        cdef list new_potential_matches = []
        cdef list items = []
        cdef bint it_pos_is_aabb
        cdef bint add

        while potential_matches:    # collect all potential items first
            new_potential_matches = []
            for i in range(len(potential_matches)):
                if potential_matches[i].aabb >= pos:
                    potential_items += potential_matches[i].items
                    positions += potential_matches[i].positions
                    new_potential_matches += potential_matches[i].child_nodes
            potential_matches = new_potential_matches
        for i in range(len(potential_items)):   # filter out invalid items
            it_pos = positions[i]
            it_pos_is_aabb = isinstance(it_pos, AABB)
            add = False
            if not pos_is_aabb and not it_pos_is_aabb:
                a = Point(tuple(pos))
                b = Point(tuple(it_pos))
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
                items.append(potential_items[i])
        return items

    cpdef bint add(self, obj, pos):
        """Return ``True`` if successful, otherwise ``False``"""
        cdef list nodes = [self]
        cdef list new_nodes = []
        cdef int i
        cdef bint first = True
        cdef Quadtree parent

        while nodes:
            new_nodes = []
            for i in range(len(nodes)):
                node = nodes[i]
                if node.aabb <= pos:
                    if node.max_level:
                        if not node.child_nodes:
                            node.populate_children()
                        new_nodes += node.child_nodes
                        parent = node
                        first = False
                        break
                    else:
                        node.items.append(obj)
                        node.positions.append(pos)
                        return True
            if not new_nodes:
                if first:
                    return False
                parent.items.append(obj)
                parent.positions.append(pos)
                return True
            nodes = new_nodes
        return False

    cpdef void populate_children(self):
        if self.child_nodes:
            return
        cdef int i
        for i in range(4):
            self.child_nodes.append(
                Quadtree(self.children[i].box, self.max_level - 1)
            )

    def __repr__(self):
        return f'{type(self).__name__}({self.__str__()})'

    def __str__(self):
        return f'({self.max_level}, {str(self.aabb)})[{self.item_count}]'


cdef class Children:
    """
    Helper class for Quadtree to store the 4 child AABB of a node

    :param box: ``Tuple[float, float, float, float]`` -> the bounding box to be
        split in quarts.
    """
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


cpdef Quadtree quadtree_from_pairs(list quadtree_pairs, int max_level=8):
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
