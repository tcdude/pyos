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
from typing import List
from typing import Optional

from engine.scene.layout import CENTER
from engine.scene.node import Node
from engine.tools.quadtree import FLOAT4
from engine.tools.quadtree import QuadTree
from engine.tools.vector import Point
from engine.tools.vector import Vector

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'


class NodePath(object):
    """
    A nested Node Graph representation, that is position and transformation
    aware. A scene graph can be constructed with a single root node, that
    represents the world space. A node can hold child nodes, that inherit
    relative depth, rotation and scale of their parent node. Any modification
    of parents, propagate the modification down to all child nodes.

    Only a root node can (should) be instantiated directly, subsequent child
    nodes should be created by calling the `Node.add_child(...)` method.
    The root node keeps track of all nodes through a quadtree data structure
    to enable operations limited to position of nodes.
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
            root=False,                     # type: Optional[bool]
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
        self.__rel_position__ = Point()     # type: Point
        self.__rel_angle__ = 0.0            # type: float
        self.__rel_scale__ = 1.0            # type: float
        self.__rel_depth__ = 0              # type: int
        self.__children__ = {}
        self.__nodes__ = []                 # type: List[Node]
        self.__is_root__ = root
        if self.__is_root__ and parent is None:
            self.__quad_tree__ = QuadTree(box, max_level)
            self.__parent__ = None
        elif parent is not None and not self.__is_root__:
            self.__quad_tree__ = parent.__quad_tree__
            self.__parent__ = parent
        else:
            raise ValueError('Node must be initialized either as root '
                             '(root=True) or as child with access to the '
                             'QuadTree from the root node (quad_tree=QuadTree)')
        self.update_relative()

    @property
    def visible(self):
        return self.__visible__

    @visible.setter
    def visible(self, value):
        if isinstance(value, bool):
            self.visible = value
        else:
            raise TypeError('visible must be of type bool')

    @property
    def relative_position(self):
        return self.__rel_position__

    @property
    def relative_angle(self):
        return self.__rel_angle__

    @property
    def relative_scale(self):
        return self.__rel_scale__

    @property
    def relative_depth(self):
        return self.__rel_depth__

    @property
    def position(self):
        return self.__position__

    @position.setter
    def position(self, value):
        if isinstance(value, (Point, Vector)):
            self.__position__ = value
        else:
            raise TypeError('position must be of type Point or Vector')

    @property
    def angle(self):
        return self.__angle__

    @angle.setter
    def angle(self, value):
        if isinstance(value, (int, float)):
            self.__angle__ = float(value)
        else:
            raise TypeError('rotation must be of type float or int')

    @property
    def scale(self):
        return self.__scale__

    @scale.setter
    def scale(self, value):
        if isinstance(value, (int, float)):
            self.__scale__ = float(value)
        else:
            raise TypeError('scale must be of type float or int')

    @property
    def depth(self):
        return self.__depth__

    @depth.setter
    def depth(self, value):
        if isinstance(value, int):
            self.__depth__ = value
        else:
            raise TypeError('depth must be of type int')

    @property
    def nodes(self):
        return self.__nodes__

    def update_relative(self):
        if self.__is_root__:
            self.__rel_position__ = Point(*self.__quad_tree__.box[:2]) + \
                                    self.position
            self.__rel_angle__ = self.angle
            self.__rel_scale__ = self.scale
            self.__rel_depth__ = self.depth
        else:
            self.__rel_position__ = self.__parent__.relative_position + \
                                    self.position
            self.__rel_angle__ = self.__parent__.relative_angle + self.angle
            self.__rel_scale__ = self.__parent__.relative_scale * self.scale
            self.__rel_depth__ = self.__parent__.relative_depth + self.depth

    def add_node(self, node):
        # type: (Node) -> int
        if isinstance(node, Node):
            self.nodes.append(node)
            return len(self.nodes) - 1
        return -1

    def traverse(self):
        self.update_relative()
        if self.visible:
            for child_id in self.__children__:
                self.__children__[child_id].traverse()

    def reparent_to(self, new_parent):
        # type: (NodePath) -> bool
        if isinstance(new_parent, NodePath):
            self.__parent__ = new_parent
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
        return NodePath(
            name=name,
            center=center,
            visible=visible,
            position=position,
            angle=angle,
            scale=scale,
            depth=depth,
            parent=self
        )

    def __repr__(self):
        return f'{type(self).__name__}({str(self.__np_name__)} / ' \
               f'{self.__np_id__})'

    def __str__(self):
        return self.__repr__()
