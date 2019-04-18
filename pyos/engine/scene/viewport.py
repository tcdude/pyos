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
from typing import List
from typing import Tuple
from typing import Union

from engine.scene.nodepath import NodePath
from engine.tools.vector import Point

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'


class ViewPort(object):
    """
    2D ViewPort to render 0..1 and 0..>=1 in world space (translated to given
    `screen_size`, where 1 unit equals the smaller part of `screen_size`).
    """
    def __init__(self, screen_size, pixel_ratio, root_node):
        # type: (Tuple[int, int], Union[float, int], NodePath) -> None
        """
        :param screen_size: available screen size for rendering
        :param pixel_ratio: pixels per world space unit
        :param root_node: a Node object that gets rendered by the ViewPort
        """
        self.__scr_size__ = screen_size
        self.__pixel_ratio__ = pixel_ratio
        self.__root_node__ = root_node
        self.__position__ = Point(0.0, 0.0)

    @property
    def position(self):
        return self.__position__

    @position.setter
    def position(self, pos):
        # type: (Point) -> None
        if isinstance(pos, Point):
            self.__position__ = pos
        else:
            raise ValueError('expected type Point')

    @property
    def screen_size(self):
        # type: () -> Tuple
        return self.__scr_size__

    @screen_size.setter
    def screen_size(self, value):
        # type: (Union[Tuple, List]) -> None
        if isinstance(value, (tuple, list)) and len(value) == 2:
            self.__scr_size__ = tuple(value)
        else:
            raise ValueError('expected Tuple/List of length 2')

    @property
    def pixel_ratio(self):
        # type: () -> float
        return self.__pixel_ratio__

    @pixel_ratio.setter
    def pixel_ratio(self, value):
        # type: (float) -> None
        if isinstance(value, (int, float)):
            self.__pixel_ratio__ = float(value)
        else:
            raise ValueError('expected type float or int')

    @property
    def root_node(self):
        # type: () -> NodePath
        return self.__root_node__  # type: NodePath

    @root_node.setter
    def root_node(self, value):
        # type: (NodePath) -> None
        if isinstance(value, NodePath):
            self.__root_node__ = value
        else:
            raise ValueError('expected type Node')

    @property
    def view_size(self):
        x, y = self.screen_size
        if x < y:
            return 1.0, y / x
        else:
            return x / y, 1.0

    def update(self):
        # type: () -> bool
        """
        Updates all dirty Nodes in the Node Graph and repositions them relative
        to the ViewPort. Only Nodes that are either inside of or overlap with
        the ViewPort are processed, leaving off screen Nodes untouched until
        they enter the ViewPort.
        :return: True if the view has changed, otherwise False.
        """
        self.root_node.traverse()
        return False

    def __repr__(self):
        return f'ViewPort({str(self.screen_size)}, {self.pixel_ratio})'

    def __str__(self):
        return self.__repr__()