"""
Provides the ViewPort to render a Scene Graph.
"""
from typing import List
from typing import Tuple
from typing import Union

from . import nodepath
from ..tools import spriteloader
from ..tools import vector

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


class ViewPort(object):
    """
    2D ViewPort to render 0..1 and 0..>=1 in world space (translated to given
    ``screen_size``, where 1 unit equals the smaller part of ``screen_size``).

    :param screen_size: available screen size for rendering
    :param asset_pixel_ratio: pixels per world space unit for scaling
    :param root_node: a Node object that gets rendered by the ViewPort
    :param sprite_loader: spriteloader.SpriteLoader instance to use
    """
    def __init__(
            self,
            screen_size,        # type: Tuple[int, int]
            asset_pixel_ratio,  # type: int
            root_node,          # type: nodepath.NodePath
            sprite_loader       # type: spriteloader.SpriteLoader
    ):
        # type: (...) -> None
        if not isinstance(screen_size, tuple):
            raise TypeError('expected Tuple for screen_size')
        if len(screen_size) != 2 or not isinstance(screen_size[0], int) or \
                not isinstance(screen_size[1], int) or screen_size[0] < 1 or \
                screen_size[1] < 1:
            raise ValueError('expected Tuple[int, int] with only positive '
                             'values')
        if not isinstance(asset_pixel_ratio, int):
            raise TypeError('expected int for asset_pixel_ratio')
        if asset_pixel_ratio < 1:
            raise ValueError('expected asset_pixel_ratio > 0')
        if not isinstance(root_node, nodepath.NodePath):
            TypeError('expected type nodepath.NodePath for root_node')
        if not isinstance(sprite_loader, spriteloader.SpriteLoader):
            TypeError('expected type spriteloader.SpriteLoader for '
                      'sprite_loader')
        self.__scr_size__ = screen_size
        self.__root_node__ = root_node
        self.__root_node__.asset_pixel_ratio = asset_pixel_ratio
        self.__root_node__.scale = asset_pixel_ratio / min(screen_size)
        self.__root_node__.sprite_loader = sprite_loader
        self.__position__ = vector.Point(0.0, 0.0)

    @property
    def position(self):
        return self.__position__

    @position.setter
    def position(self, pos):
        # type: (vector.Point) -> None
        if isinstance(pos, vector.Point):
            self.__position__ = pos
        else:
            raise TypeError('expected type vector.Point')

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
            raise TypeError('expected Tuple/List of length 2')

    @property
    def asset_pixel_ratio(self):
        # type: () -> float
        return self.root_node.asset_pixel_ratio

    @asset_pixel_ratio.setter
    def asset_pixel_ratio(self, value):
        # type: (int) -> None
        self.root_node.asset_pixel_ratio = value

    @property
    def root_node(self):
        # type: () -> nodepath.NodePath
        return self.__root_node__  # type: nodepath.NodePath

    @root_node.setter
    def root_node(self, value):
        # type: (nodepath.NodePath) -> None
        if isinstance(value, nodepath.NodePath):
            self.__root_node__ = value
        else:
            raise TypeError('expected type Node')

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
        return f'{type(self).__name__}({str(self.screen_size)}, ' \
               f'{self.asset_pixel_ratio})'

    def __str__(self):
        return self.__repr__()
