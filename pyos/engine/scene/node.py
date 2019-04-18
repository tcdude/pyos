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
import os
from typing import List
from typing import Optional
from typing import Tuple

from sdl2.ext import Entity
from sdl2.ext import Sprite
from sdl2.ext import World

from engine.scene.nodepath import NodePath

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'


class PlaceHolderEntity(Entity):
    def __init__(
            self,
            world,      # type: World
            sprite,     # type: Sprite
            x=0,        # type: Optional[int]
            y=0,        # type: Optional[int]
            d=0         # type: Optional[int]
    ):
        # type: (...) -> None
        self.__world__ = world
        self.sprite = sprite
        self.sprite.position = x, y
        self.sprite.depth = d


class Node(object):
    def __init__(self, node_path, name=None):
        # type: (NodePath, Optional[str]) -> None
        if not isinstance(node_path, NodePath):
            raise ValueError('invalid argument for node_path')
        self.__node_path__ = node_path
        self.__node_name__ = name or 'Unnamed Node'

    @property
    def size(self):
        return 0, 0

    @property
    def node_path(self):
        return self.__node_path__

    @property
    def name(self):
        return self.__node_name__

    def __repr__(self):
        return f'{type(self).__name__}({self.name}, {self.size})'

    def __str__(self):
        return self.__repr__()


class ImageNode(Node):
    def __init__(self, node_path, name=None, image=None):
        super(ImageNode, self).__init__(node_path, name)
        self.__images__ = []            # type: List[str]
        self.__current_index__ = -1
        self.__entity__ = None
        if image is not None:
            self.add_image(image)

    def update(self, pos=None, scale=None, angle=None, depth=None):
        pass

    @property
    def size(self):
        # type: () -> Tuple[int, int]
        if self.__entity__ is None:
            return 0, 0
        return self.__entity__.sprite.size

    @property
    def entity(self):
        # type: () -> PlaceHolderEntity
        return self.__entity__

    @entity.setter
    def entity(self, value):
        # type: (PlaceHolderEntity) -> None
        if isinstance(value, PlaceHolderEntity):
            self.__entity__ = value
        else:
            raise ValueError('expected PlaceHolderEntity')

    def add_image(self, image):
        # type: (str) -> None
        if os.path.isfile(image):
            self.__images__.append(image)
        else:
            raise FileNotFoundError(f'unable to locate "{image}"')

    def pop(self, index):
        # type: (int) -> str
        if -1 < index < len(self.__images__):
            return self.__images__.pop(index)
        else:
            raise IndexError

    def __getitem__(self, item):
        if -1 < item < len(self.__images__):
            return self.__images__[item]
        raise IndexError
