"""
Provides the NodePath class for the Scene Graph.
"""

import uuid
from typing import Any
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from . import node
from .. import tools
from ..tools import aabb
from ..tools import quadtree
from ..tools import spriteloader

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

CENTER = tools.CENTER
TOP_LEFT = tools.TOP_LEFT
BOTTOM_RIGHT = tools.BOTTOM_RIGHT


class NodePath(object):
    """
    Structural part of the Scene Graph.
    A scene starts at a root NodePath, that maintains a QuadTree for fast access
    of NodePath and Node objects. New NodePath objects can be created by calling
    the ``attach_new_node_path()`` method of the appropriate "Parent" NodePath.
    A NodePath can hold a Node type object and keeps track of position, scale,
    rotation and depth. The properties propagate from the root NodePath down to
    all children in the graph.

    :param name: Optional name
    :param center: Specifies where the origin lies (CENTER=0, TOP_LEFT=1,
        BOTTOM_RIGHT=2) as int (default=TOP_LEFT)
    :param visible: Whether the NodePath is visible (default=True)
    :param position: Optional Point -> position offset relative to its parent.
    :param angle: Optional float -> angle of rotation in degrees relative to its
        parent.
    :param scale: Optional float -> scale relative to its parent.
    :param depth: Optional int -> depth relative to its parent.
    :param parent: Optional NodePath -> If specified, the instance will be a
        child of ``parent`` and inherit position, scale, rotation and depth.
    :param max_level: Optional int -> maximum levels of nesting of the quadtree.
    """
    def __init__(
            self,
            name=None,                      # type: Optional[str]
            center=TOP_LEFT,                # type: Optional[int]
            visible=True,                   # type: Optional[bool]
            position=tools.Point(0, 0),     # type: Optional[tools.Point]
            angle=0.0,                      # type: Optional[float]
            scale=1.0,                      # type: Optional[float]
            depth=1,                        # type: Optional[int]
            parent=None,                    # type: Optional[NodePath]
            max_level=8                     # type: Optional[int]
    ):
        # type: (...) -> None
        self._np_id = uuid.uuid4().hex
        self._np_name = name or 'Unnamed NodePath'
        self._center = center
        self._visible = visible
        self._position = position
        self._angle = angle
        self._scale = scale
        self._depth = depth
        self._rotation_center = None
        self._rel_position = tools.Point()
        self._rel_angle = 0.0
        self._rel_scale = 1.0
        self._rel_depth = 0
        self._asset_pixel_ratio = 1
        self._dummy_size = None
        self._children = []
        self._node = node.Node(self)
        self._root_nodepath = None
        self._tags = {}
        self._dirty = True
        self._max_level = max_level
        if parent is None:
            self._is_root = True
            self._quadtree = None      # Only relevant after first traverse
            self._parent = None
            self._sprite_loader = None
            self._root_nodepath = self
        else:
            self._is_root = False
            self._quadtree = parent._quadtree
            self._parent = parent
            self._root_nodepath = parent.root_nodepath
            self._sprite_loader = parent._sprite_loader
            if not self._parent.dirty:
                self._parent.dirty = True
        self.update_relative()

    @property
    def root_nodepath(self):
        return self._root_nodepath

    @root_nodepath.setter
    def root_nodepath(self, value):
        if isinstance(value, NodePath):
            self._root_nodepath = value
        else:
            raise TypeError('expected type NodePath for root_node')

    @property
    def visible(self):
        # type: () -> bool
        """``bool``"""
        return self._visible

    @visible.setter
    def visible(self, value):
        # type: (bool) -> None
        if isinstance(value, bool):
            if value != self._visible:
                self._visible = value
                self.dirty = True
        else:
            raise TypeError('visible must be of type bool')

    @property
    def relative_position(self):
        # type: () -> tools.Point
        """``engine.tools.vector.Point``"""

        return self._rel_position

    @property
    def relative_angle(self):
        # type: () -> float
        """``float``"""
        return self._rel_angle

    @property
    def relative_scale(self):
        # type: () -> float
        """``float``"""
        return self._rel_scale

    @property
    def relative_depth(self):
        # type: () -> int
        """``int``"""
        return self._rel_depth

    @property
    def position(self):
        # type: () -> tools.Point
        """``engine.tools.vector.Point``"""
        return self._position

    @position.setter
    def position(self, value):
        # type: (Union[tools.Point, tools.Vector, tuple]) -> None
        if isinstance(value, (tools.Point, tools.Vector)):
            self._position = value
        elif isinstance(value, tuple) and len(value) == 2 and \
                isinstance(value[0], float) and isinstance(value[1], float):
            self._position = tools.Point(value)
        else:
            raise TypeError('position must be of type Point, Vector or '
                            'Tuple[float, float]')
        self.dirty = True

    @property
    def angle(self):
        # type: () -> float
        """``float``"""
        return self._angle

    @angle.setter
    def angle(self, value):
        # type: (Union[int, float]) -> None
        if isinstance(value, (int, float)):
            self._angle = float(value)
            self.dirty = True
        else:
            raise TypeError('rotation must be of type float or int')

    @property
    def scale(self):
        # type: () -> float
        """``float``"""
        return self._scale

    @scale.setter
    def scale(self, value):
        # type: (Union[int, float]) -> None
        if isinstance(value, (int, float)):
            self._scale = float(value)
            self.dirty = True
        else:
            raise TypeError('scale must be of type float or int')

    @property
    def depth(self):
        # type: () -> int
        """``int``"""
        return self._depth

    @depth.setter
    def depth(self, value):
        # type: (int) -> None
        if isinstance(value, int):
            self._depth = value
            self.dirty = True
        else:
            raise TypeError('depth must be of type int')

    @property
    def center(self):
        # type: () -> int
        """``int`` in ``engine.tools.CENTER/.TOP_LEFT/.BOTTOM_RIGHT``"""
        return self._center

    @center.setter
    def center(self, value):
        if value in (CENTER, TOP_LEFT, BOTTOM_RIGHT):
            self._center = value
            self.dirty = True
        else:
            raise ValueError(f'expected value to be in (CENTER={CENTER}, '
                             f'TOP_LEFT={TOP_LEFT}, BOTTOM_RIGHT='
                             f'{BOTTOM_RIGHT}) got "{repr(value)}" instead')

    @property
    def rotation_center(self):
        # type: () -> Union[None, Tuple[int, int]]
        """``Union[None, Tuple[int, int]]``"""
        return self._rotation_center

    @rotation_center.setter
    def rotation_center(self, value):
        # type: (Union[None, Tuple[int, int]]) -> None
        if isinstance(value, tuple) and len(value) == 2 and \
                isinstance(value[0], int) and isinstance(value[1], int):
            self._rotation_center = value
        elif value is None:
            self._rotation_center = None
        else:
            raise TypeError('expected Tuple[int, int] or None')
        self.dirty = True

    @property
    def asset_pixel_ratio(self):
        # type: () -> int
        """``int``"""
        if self._is_root:
            return self._asset_pixel_ratio
        if self.root_nodepath is None:
            raise ValueError('unable to retrieve asset_pixel_ratio, '
                             'root_nodepath property is None')
        return self.root_nodepath.asset_pixel_ratio

    @asset_pixel_ratio.setter
    def asset_pixel_ratio(self, value):
        # type: (int) -> None
        if self._is_root:
            if isinstance(value, int) and value > 0:
                if value > 0:
                    self._asset_pixel_ratio = value
                    self.dirty = True
                else:
                    raise ValueError('expected int > 0')
            else:
                raise TypeError('expected type int')
        else:
            raise ValueError('asset_pixel_ratio property can only be set on a '
                             'NodePath marked as root')

    @property
    def sprite_loader(self):
        # type: () -> spriteloader.SpriteLoader
        """``engine.tools.spriteloader.SpriteLoader``"""
        if self._is_root:
            return self._sprite_loader
        if self.root_nodepath is None:
            raise ValueError('unable to retrieve sprite_loader, root_nodepath '
                             'property is None')
        return self.root_nodepath.sprite_loader

    @sprite_loader.setter
    def sprite_loader(self, value):
        # type: (spriteloader.SpriteLoader) -> None
        if self._is_root:
            if isinstance(value, spriteloader.SpriteLoader):
                self._sprite_loader = value
                self.dirty = True
            else:
                raise TypeError('expected type SpriteLoader')
        else:
            raise ValueError('sprite_loader property can only be set on a '
                             'NodePath marked as root')

    @property
    def size(self):
        # type: () -> Tuple[float, float]
        """``Tuple[float, float]``"""
        if self.node.size is None:
            if self._dummy_size is None:
                return 0.0, 0.0
            return self._dummy_size
        ns = tools.Vector(self.node.size) / self.asset_pixel_ratio
        return ns.x * self.relative_scale, ns.y * self.relative_scale

    @property
    def children(self):
        # type: () -> List[NodePath]
        """``List[NodePath]``"""
        return self._children

    @property
    def node(self):
        # type: () -> node.Node
        """``Node``"""
        return self._node

    @node.setter
    def node(self, value):
        # type: (node.Node) -> None
        if isinstance(value, node.Node):
            self._node = value
            self.dirty = True
        else:
            raise TypeError(f'expected type Node, got {type(value).__name__}')

    @property
    def quadtree(self):
        # type: () -> quadtree.Quadtree
        """``engine.tools.quadtree.Quadtree``"""
        if self._is_root:
            return self._quadtree
        if self.root_nodepath is None:
            raise ValueError('unable to retrieve quadtree, root_nodepath '
                             'property is None')
        return self.root_nodepath.quadtree

    @quadtree.setter
    def quadtree(self, value):
        # type: (quadtree.Quadtree) -> None
        if self._is_root:
            if isinstance(value, quadtree.Quadtree):
                self._quadtree = value
                self.dirty = True
            else:
                raise TypeError('expected type Quadtree')
        else:
            raise ValueError('quadtree property can only be set on a NodePath '
                             'that is marked as root')

    @property
    def dirty(self):
        # type: () -> bool
        """``bool``"""
        return self._dirty

    @dirty.setter
    def dirty(self, value):
        # type: (bool) -> None
        if not isinstance(value, bool):
            raise TypeError('expected bool')
        if self.root_nodepath is None:
            raise ValueError('unable to retrieve sprite_loader, root_nodepath '
                             'property is None')
        self._dirty = value
        if value and not self._is_root:   # set dirty at root
            self.root_nodepath.dirty = value

    def set_dummy_size(self, size):
        # type: (Union[tools.Vector, tools.Point, Tuple[float, float]]) -> None
        """
        Sets a dummy size for the NodePath.

        :param size: ``Union[Vector, Point, Tuple[int, int]]``
        """
        if not isinstance(size, tuple):
            size = tuple(size)
        self._dummy_size = size
        self.dirty = True

    def update_relative(self):
        """Update the relative attributes in respect to ``parent``."""
        if self.center == CENTER:
            offset = tools.Point(self.size) / -2
        elif self.center == TOP_LEFT:
            offset = tools.Point()
        elif self.center == BOTTOM_RIGHT:
            offset = tools.Point() - tools.Point(self.size)
        else:
            raise ValueError('invalid value in property NodePath.center')

        if self._is_root:
            self._rel_position = self.position + offset
            self._rel_angle = self.angle
            self._rel_scale = self.scale
            self._rel_depth = self.depth
        else:
            if self._parent.relative_angle:
                rel_pos = self.position.rotate(
                    self._parent.relative_angle
                ).aspoint()
            else:
                rel_pos = self.position
            self._rel_position = (
                    self._parent.relative_position + rel_pos + offset
            )
            self._rel_angle = self._parent.relative_angle + self.angle
            self._rel_scale = self._parent.relative_scale * self.scale
            self._rel_depth = self._parent.relative_depth + self.depth

    def traverse(self):
        # type: () -> Union[List[Tuple[aabb.AABB, Any]], bool]
        """
        Traverse the scene graph to update relative properties and update the
        quadtree of the root NodePath
        """
        if self._is_root and not self.dirty:
            return False
        self.update_relative()
        self.dirty = False
        box = tuple(self.relative_position)
        box += tuple(self.relative_position + tools.Point(*self.size))
        quadtree_pairs = [(aabb.AABB(box), self)]
        if self.visible:
            for child in self.children:     # type: NodePath
                quadtree_pairs += child.traverse()
        if self._is_root:
            qt = quadtree.quadtree_from_pairs(quadtree_pairs, self._max_level)
            if qt is not None:
                self.quadtree = qt
                return True
            return False
        return quadtree_pairs

    def reparent_to(self, new_parent):
        # type: (NodePath) -> bool
        """
        Reparent this instance to another parent NodePath.

        :param new_parent: ``NodePath`` -> The new parent.
        :return: ``bool`` -> success.
        """
        if isinstance(new_parent, NodePath):
            if self._parent is not None:
                self._parent.remove_node_path(self)
            self._parent = new_parent
            self._parent.children.append(self)
            self.quadtree = new_parent.quadtree
            self._is_root = False
            self.dirty = True
            self.root_nodepath = self._parent.root_nodepath
            return True
        return False

    def attach_new_node_path(
            self,
            name=None,                      # type: Optional[str]
            center=None,                    # type: Optional[Union[None, int]]
            visible=True,                   # type: Optional[bool]
            position=tools.Point(0, 0),     # type: Optional[tools.Point]
            angle=0.0,                      # type: Optional[float]
            scale=1.0,                      # type: Optional[float]
            depth=0,                        # type: Optional[int]
    ):
        # type: (...) -> NodePath
        """
        Attach and return a new child ``NodePath`` to this instance.

        :param name: Optional ``str`` -> name of the new ``NodePath``
        :param center: Optional ``int`` -> origin of the new ``NodePath``
        :param visible: Optional ``bool``
        :param position: Optional ``engine.tools.vector.Point``
        :param angle: Optional ``float``
        :param scale: Optional ``float``
        :param depth: Optional ``int``
        :return: ``engine.scene.nodepath.NodePath``
        """
        np = NodePath(
            name=name,
            center=center or self.center,
            visible=visible,
            position=position,
            angle=angle,
            scale=scale,
            depth=depth,
            parent=self
        )
        self.children.append(np)
        self.dirty = True
        return np

    def query(self, q_aabb, overlap=True):
        # type: (aabb.AABB, Optional[bool]) -> List[NodePath]
        """
        Return a list of ``NodePath`` instances that lie within or overlap with
        the given ``AABB``.

        :param q_aabb: ``engine.tools.aabb.AABB`` -> bounding box to query.
        :param overlap: Optional ``bool`` -> whether to include or exclude
            overlapping ``NodePath`` instances.
        :return: ``List[NodePath]``
        """
        if self._is_root:
            if self.dirty:
                self.traverse()
            if self.quadtree is not None:
                return self.quadtree.get_items(q_aabb, overlap)
            raise ValueError('unable to populate a Quadtree.')
        return self._parent.query(q_aabb, overlap)

    def remove_node_path(self, np):
        # type: (NodePath) -> bool
        """
        Removes the passed ``NodePath``. Return ``True`` if ``np`` is a child,
        otherwise ``False``.

        :param np: ``NodePath``
        :return: ``bool``
        """
        if np in self.children:
            self.children.pop(self.children.index(np))
            self.dirty = True
            return True
        return False

    def pop(self, item):
        return self._tags.pop(item)

    def __getitem__(self, item):
        return self._tags[item]

    def __setitem__(self, key, value):
        self._tags[key] = value

    def __len__(self):
        return len(self._tags)

    def __contains__(self, item):
        return self._tags.__contains__(item)

    def __repr__(self):
        return f'{type(self).__name__}({str(self._np_name)})'

    def __str__(self):
        return self.__repr__()
