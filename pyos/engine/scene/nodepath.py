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
        BOTTOM_RIGHT=2) as int (default=CENTER)
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
            center=CENTER,                  # type: Optional[int]
            visible=True,                   # type: Optional[bool]
            position=tools.Point(0, 0),     # type: Optional[tools.Point]
            angle=0.0,                      # type: Optional[float]
            scale=1.0,                      # type: Optional[float]
            depth=1,                        # type: Optional[int]
            parent=None,                    # type: Optional[NodePath]
            max_level=8                     # type: Optional[int]
    ):
        # type: (...) -> None
        self.__np_id = uuid.uuid4().hex
        self.__np_name = name or 'Unnamed NodePath'
        self.__center = center
        self.__visible = visible
        self.__position = position
        self.__angle = angle
        self.__scale = scale
        self.__depth = depth
        self.__rotation_center = None
        self.__rel_position = tools.Point()
        self.__rel_angle = 0.0
        self.__rel_scale = 1.0
        self.__rel_depth = 0
        self.__asset_pixel_ratio = 1
        self.__children = []
        self.__node = node.Node(self)
        self.__tags = {}
        self.__dirty = True
        self.__max_level = max_level
        if parent is None:
            self.__is_root = True
            self.__quadtree = None      # Only relevant after first traverse
            self.__parent = None
            self.__sprite_loader = None
        else:
            self.__is_root = False
            self.__quadtree = parent.__quadtree
            self.__parent = parent
            self.__sprite_loader = parent.__sprite_loader
        self.update_relative()

    @property
    def visible(self):
        # type: () -> bool
        return self.__visible

    @visible.setter
    def visible(self, value):
        # type: (bool) -> None
        if isinstance(value, bool):
            self.visible = value
        else:
            raise TypeError('visible must be of type bool')

    @property
    def relative_position(self):
        # type: () -> tools.Point
        return self.__rel_position

    @property
    def relative_angle(self):
        # type: () -> float
        return self.__rel_angle

    @property
    def relative_scale(self):
        # type: () -> float
        return self.__rel_scale

    @property
    def relative_depth(self):
        # type: () -> int
        return self.__rel_depth

    @property
    def position(self):
        # type: () -> tools.Point
        return self.__position

    @position.setter
    def position(self, value):
        # type: (Union[tools.Point, tools.Vector]) -> None
        if isinstance(value, (tools.Point, tools.Vector)):
            self.__position = value
        else:
            raise TypeError('position must be of type Point or Vector')

    @property
    def angle(self):
        # type: () -> float
        return self.__angle

    @angle.setter
    def angle(self, value):
        # type: (Union[int, float]) -> None
        if isinstance(value, (int, float)):
            self.__angle = float(value)
        else:
            raise TypeError('rotation must be of type float or int')

    @property
    def scale(self):
        # type: () -> float
        return self.__scale

    @scale.setter
    def scale(self, value):
        # type: (Union[int, float]) -> None
        if isinstance(value, (int, float)):
            self.__scale = float(value)
        else:
            raise TypeError('scale must be of type float or int')

    @property
    def depth(self):
        # type: () -> int
        return self.__depth

    @depth.setter
    def depth(self, value):
        # type: (int) -> None
        if isinstance(value, int):
            self.__depth = value
        else:
            raise TypeError('depth must be of type int')

    @property
    def center(self):
        return self.__center

    @center.setter
    def center(self, value):
        if value in (CENTER, TOP_LEFT, BOTTOM_RIGHT):
            self.__center = value
        else:
            raise ValueError(f'expected value to be in (CENTER={CENTER}, '
                             f'TOP_LEFT={TOP_LEFT}, BOTTOM_RIGHT='
                             f'{BOTTOM_RIGHT}) got "{repr(value)}" instead')

    @property
    def rotation_center(self):
        return self.__rotation_center

    @rotation_center.setter
    def rotation_center(self, value):
        if isinstance(value, tuple) and len(value) == 2 and \
           isinstance(value[0], int) and isinstance(value[1], int):
            self.__rotation_center = value
        elif value is None:
            self.__rotation_center = None
        else:
            raise TypeError('expected Tuple[int, int] or None')

    @property
    def asset_pixel_ratio(self):
        # type: () -> int
        return self.__asset_pixel_ratio

    @asset_pixel_ratio.setter
    def asset_pixel_ratio(self, value):
        # type: (int) -> None
        if isinstance(value, int):
            if value > 0:
                self.asset_pixel_ratio = value
                for child in self.children:     # type: NodePath
                    child.asset_pixel_ratio = value
            else:
                raise ValueError('expected int > 0')
        else:
            raise TypeError('expected type int')

    @property
    def sprite_loader(self):
        # type: () -> spriteloader.SpriteLoader
        if self.__sprite_loader is None:
            raise ValueError('sprite_loader not set')
        return self.__sprite_loader

    @sprite_loader.setter
    def sprite_loader(self, value):
        # type: (spriteloader.SpriteLoader) -> None
        if isinstance(value, spriteloader.SpriteLoader):
            self.__sprite_loader = value
            for child in self.children:     # type: NodePath
                child.sprite_loader = value
        else:
            raise TypeError('expected type SpriteLoader')

    @property
    def size(self):
        # type: () -> Tuple[float, float]
        ns = tools.Vector(*self.node.size) / self.asset_pixel_ratio
        return ns.x * self.relative_scale, ns.y * self.relative_scale

    @property
    def children(self):
        # type: () -> List[NodePath]
        return self.__children

    @property
    def node(self):
        # type: () -> node.Node
        return self.__node

    @node.setter
    def node(self, value):
        # type: (node.Node) -> None
        if isinstance(value, node.Node):
            self.__node = value
        else:
            raise TypeError(f'expected type Node, got {type(value).__name__}')

    @property
    def quadtree(self):
        # type: () -> quadtree.Quadtree
        return self.__quadtree

    @quadtree.setter
    def quadtree(self, value):
        # type: (quadtree.Quadtree) -> None
        if isinstance(value, quadtree.Quadtree):
            if self.__is_root:
                self.__quadtree = value
            else:
                self.__parent.quadtree = value
        else:
            raise TypeError('expected type Quadtree')

    @property
    def dirty(self):
        # type: () -> bool
        return self.__dirty

    @dirty.setter
    def dirty(self, value):
        # type: (bool) -> None
        if not isinstance(value, bool):
            raise TypeError('expected bool')
        if value and not self.__is_root:   # propagate dirty to root
            self.__parent.dirty = value
        self.__dirty = value

    def set_dummy_size(self, size):
        # type: (Union[tools.Vector, tools.Point, Tuple[float, float]]) -> None
        if isinstance(size, tuple):
            size = tools.Vector(*size)
        ns = size * self.asset_pixel_ratio
        ns /= self.relative_scale
        self.node.set_dummy_size(tuple(ns))

    def update_relative(self):
        if self.__is_root:
            self.__rel_position = self.position
            self.__rel_angle = self.angle
            self.__rel_scale = self.scale
            self.__rel_depth = self.depth
        else:
            if self.__parent.angle:
                rel_pos = self.position.rotate(self.__parent.angle).aspoint()
            else:
                rel_pos = self.position
            self.__rel_position = self.__parent.relative_position + rel_pos
            self.__rel_angle = self.__parent.relative_angle + self.angle
            self.__rel_scale = self.__parent.relative_scale * self.scale
            self.__rel_depth = self.__parent.relative_depth + self.depth

    def traverse(self):
        # type: () -> Union[List[Tuple[aabb.AABB, Any]], bool]
        """
        Traverse the scene graph to update relative properties and update the
        quadtree of the root NodePath
        """
        if self.__is_root and not self.dirty:
            return False
        self.update_relative()
        self.dirty = False
        box = tuple(self.relative_position)
        box += tuple(self.relative_position + tools.Point(*self.size))
        quadtree_pairs = [(aabb.AABB(box), self)]
        if self.visible:
            for child in self.children:     # type: NodePath
                quadtree_pairs += child.traverse()
        if self.__is_root:
            qt = quadtree.quadtree_from_pairs(quadtree_pairs, self.__max_level)
            if qt is not None:
                self.quadtree = qt
                return True
            return False
        return quadtree_pairs

    def reparent_to(self, new_parent):
        # type: (NodePath) -> bool
        if isinstance(new_parent, NodePath):
            if self.__parent is not None:
                self.__parent.remove_node_path(self)
            self.__parent = new_parent
            self.__parent.children.append(self)
            self.quadtree = new_parent.quadtree
            self.__is_root = False
            return True
        return False

    def attach_new_node_path(
            self,
            name=None,                      # type: Optional[str]
            center=CENTER,                  # type: Optional[int]
            visible=True,                   # type: Optional[bool]
            position=tools.Point(0, 0),     # type: Optional[tools.Point]
            angle=0.0,                      # type: Optional[float]
            scale=1.0,                      # type: Optional[float]
            depth=0,                        # type: Optional[int]
    ):
        # type: (...) -> NodePath
        np = NodePath(
            name=name,
            center=center,
            visible=visible,
            position=position,
            angle=angle,
            scale=scale,
            depth=depth,
            parent=self
        )
        self.children.append(np)
        return np

    def query(self, q_aabb, overlap=True):
        return self.quadtree.get_items(q_aabb, overlap)

    def remove_node_path(self, np):
        if np in self.children:
            self.children.pop(self.children.index(np))

    def __getitem__(self, item):
        return self.__tags[item]

    def __setitem__(self, key, value):
        self.__tags[key] = value

    def __len__(self):
        return len(self.__tags)

    def __contains__(self, item):
        return self.__tags.__contains__(item)

    def __repr__(self):
        return f'{type(self).__name__}({str(self.__np_name)} / ' \
               f'{self.__np_id})'

    def __str__(self):
        return self.__repr__()
