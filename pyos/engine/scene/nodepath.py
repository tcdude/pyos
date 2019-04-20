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

import uuid
from typing import Any
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from engine.scene.layout import CENTER
from engine.scene.layout import TOP_LEFT
from engine.scene.layout import BOTTOM_RIGHT
from engine.scene.node import Node
from engine.tools.aabb import AABB
from engine.tools.quadtree import FLOAT4
from engine.tools.quadtree import quadtree_from_pairs
from engine.tools.quadtree import Quadtree
from engine.tools.spriteloader import SpriteLoader
from engine.tools.vector import Point
from engine.tools.vector import Vector

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'


class NodePath(object):
    """
    Structural part of the Scene Graph. A scene starts at a root NodePath,
    that maintains a QuadTree for fast access of NodePath and Node objects.
    New NodePath objects can be created by calling the `attach_new_node_path()`
    method of the appropriate "Parent" NodePath.
    A NodePath can hold a Node type object and keeps track of position, scale,
    rotation and depth. The properties propagate from the root NodePath down to
    all children in the graph.
    """
    def __init__(
            self,
            name=None,                      # type: Optional[str]
            center=CENTER,                  # type: Optional[int]
            visible=True,                   # type: Optional[bool]
            position=Point(0, 0),           # type: Optional[Point]
            angle=0.0,                      # type: Optional[float]
            scale=1.0,                      # type: Optional[float]
            depth=0,                        # type: Optional[int]
            parent=None,                    # type: Optional[NodePath]
            box=(0.0, 0.0, 1.0, 1.0),       # type: Optional[FLOAT4]
            max_level=8                     # type: Optional[int]
    ):
        # type: (...) -> None
        self.__np_id__ = uuid.uuid4().hex
        self.__np_name__ = name or 'Unnamed NodePath'
        self.__center__ = center
        self.__visible__ = visible
        self.__position__ = position
        self.__angle__ = angle
        self.__scale__ = scale
        self.__depth__ = depth
        self.__rotation_center__ = None
        self.__rel_position__ = Point()
        self.__rel_angle__ = 0.0
        self.__rel_scale__ = 1.0
        self.__rel_depth__ = 0
        self.__asset_pixel_ratio__ = 1
        self.__children__ = []
        self.__node__ = Node(self)
        self.__dirty__ = True
        if parent is None:
            self.__is_root__ = True
            self.__quadtree__ = Quadtree(box, max_level)
            self.__parent__ = None
            self.__sprite_loader__ = None
        else:
            self.__is_root__ = False
            self.__quadtree__ = parent.__quadtree__
            self.__parent__ = parent
            self.__sprite_loader__ = parent.__sprite_loader__
        self.update_relative()

    @property
    def visible(self):
        # type: () -> bool
        return self.__visible__

    @visible.setter
    def visible(self, value):
        # type: (bool) -> None
        if isinstance(value, bool):
            self.visible = value
        else:
            raise TypeError('visible must be of type bool')

    @property
    def relative_position(self):
        # type: () -> Point
        return self.__rel_position__

    @property
    def relative_angle(self):
        # type: () -> float
        return self.__rel_angle__

    @property
    def relative_scale(self):
        # type: () -> float
        return self.__rel_scale__

    @property
    def relative_depth(self):
        # type: () -> int
        return self.__rel_depth__

    @property
    def position(self):
        # type: () -> Point
        return self.__position__

    @position.setter
    def position(self, value):
        # type: (Union[Point, Vector]) -> None
        if isinstance(value, (Point, Vector)):
            self.__position__ = value
        else:
            raise TypeError('position must be of type Point or Vector')

    @property
    def angle(self):
        # type: () -> float
        return self.__angle__

    @angle.setter
    def angle(self, value):
        # type: (Union[int, float]) -> None
        if isinstance(value, (int, float)):
            self.__angle__ = float(value)
        else:
            raise TypeError('rotation must be of type float or int')

    @property
    def scale(self):
        # type: () -> float
        return self.__scale__

    @scale.setter
    def scale(self, value):
        # type: (Union[int, float]) -> None
        if isinstance(value, (int, float)):
            self.__scale__ = float(value)
        else:
            raise TypeError('scale must be of type float or int')

    @property
    def depth(self):
        # type: () -> int
        return self.__depth__

    @depth.setter
    def depth(self, value):
        # type: (int) -> None
        if isinstance(value, int):
            self.__depth__ = value
        else:
            raise TypeError('depth must be of type int')

    @property
    def center(self):
        return self.__center__

    @center.setter
    def center(self, value):
        if value in (CENTER, TOP_LEFT, BOTTOM_RIGHT):
            self.__center__ = value
        else:
            raise ValueError(f'expected value to be in (CENTER={CENTER}, '
                             f'TOP_LEFT={TOP_LEFT}, BOTTOM_RIGHT='
                             f'{BOTTOM_RIGHT}) got "{repr(value)}" instead')

    @property
    def rotation_center(self):
        return self.__rotation_center__

    @rotation_center.setter
    def rotation_center(self, value):
        if isinstance(value, tuple) and len(value) == 2 and \
           isinstance(value[0], int) and isinstance(value[1], int):
            self.__rotation_center__ = value
        elif value is None:
            self.__rotation_center__ = None
        else:
            raise TypeError('expected Tuple[int, int] or None')

    @property
    def asset_pixel_ratio(self):
        # type: () -> int
        return self.__asset_pixel_ratio__

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
        # type: () -> SpriteLoader
        if self.__sprite_loader__ is None:
            raise ValueError('sprite_loader not set')
        return self.__sprite_loader__

    @sprite_loader.setter
    def sprite_loader(self, value):
        # type: (SpriteLoader) -> None
        if isinstance(value, SpriteLoader):
            self.__sprite_loader__ = value
            for child in self.children:     # type: NodePath
                child.sprite_loader = value
        else:
            raise TypeError('expected type SpriteLoader')

    @property
    def size(self):
        # type: () -> Tuple[float, float]
        ns = Vector(*self.node.size) / self.asset_pixel_ratio
        return ns.x * self.relative_scale, ns.y * self.relative_scale

    @property
    def children(self):
        # type: () -> List[NodePath]
        return self.__children__

    @property
    def node(self):
        # type: () -> Node
        return self.__node__

    @node.setter
    def node(self, value):
        # type: (Node) -> None
        if isinstance(value, Node):
            self.__node__ = value
        else:
            raise TypeError(f'expected type Node, got {type(value).__name__}')

    @property
    def quadtree(self):
        # type: () -> Quadtree
        return self.__quadtree__

    @quadtree.setter
    def quadtree(self, value):
        # type: (Quadtree) -> None
        if isinstance(value, Quadtree):
            if self.__is_root__:
                self.__quadtree__ = value
            else:
                self.__parent__.quadtree = value
        else:
            raise TypeError('expected type Quadtree')

    @property
    def dirty(self):
        # type: () -> bool
        return self.__dirty__

    @dirty.setter
    def dirty(self, value):
        # type: (bool) -> None
        if not isinstance(value, bool):
            raise TypeError('expected bool')
        if value and not self.__is_root__:   # propagate dirty to root
            self.__parent__.dirty = value
        self.__dirty__ = value

    def update_relative(self):
        if self.__is_root__:
            self.__rel_position__ = self.position
            self.__rel_angle__ = self.angle
            self.__rel_scale__ = self.scale
            self.__rel_depth__ = self.depth
        else:
            if self.__parent__.angle:
                rel_pos = self.position.rotate(self.__parent__.angle).aspoint()
            else:
                rel_pos = self.position
            self.__rel_position__ = self.__parent__.relative_position + rel_pos
            self.__rel_angle__ = self.__parent__.relative_angle + self.angle
            self.__rel_scale__ = self.__parent__.relative_scale * self.scale
            self.__rel_depth__ = self.__parent__.relative_depth + self.depth

    def traverse(self):
        # type: () -> Union[List[Tuple[AABB, Any]], bool]
        """
        Traverse the scene graph to update relative properties and update the
        quadtree of the root NodePath
        """
        if self.__is_root__ and not self.dirty:
            return False
        self.update_relative()
        self.dirty = False
        box = tuple(self.relative_position)
        box += tuple(self.relative_position + Point(*self.size))
        quadtree_pairs = [(AABB(box), self)]
        if self.visible:
            for child in self.children:     # type: NodePath
                quadtree_pairs += child.traverse()
        if self.__is_root__:
            qt = quadtree_from_pairs(quadtree_pairs)
            if qt is not None:
                self.quadtree = qt
                return True
            return False
        return quadtree_pairs

    def reparent_to(self, new_parent):
        # type: (NodePath) -> bool
        if isinstance(new_parent, NodePath):
            if self.__parent__ is not None:
                self.__parent__.remove(self)
            self.__parent__ = new_parent
            self.__parent__.children.append(self)
            self.quadtree = new_parent.quadtree
            self.__is_root__ = False
            return True
        return False

    def attach_new_node_path(
            self,
            name=None,              # type: Optional[str]
            center=CENTER,          # type: Optional[int]
            visible=True,           # type: Optional[bool]
            position=Point(0, 0),   # type: Optional[Point]
            angle=0.0,              # type: Optional[float]
            scale=1.0,              # type: Optional[float]
            depth=0,                # type: Optional[int]
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

    def query(self, aabb, overlap=True):
        return self.quadtree.get_items(aabb, overlap)

    def remove(self, np):
        if np in self.children:
            self.children.pop(self.children.index(np))

    def __repr__(self):
        return f'{type(self).__name__}({str(self.__np_name__)} / ' \
               f'{self.__np_id__})'

    def __str__(self):
        return self.__repr__()
