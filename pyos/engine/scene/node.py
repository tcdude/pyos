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

from PIL import Image
from sdl2.ext import Entity
from sdl2.ext import TextureSprite
from sdl2.ext import World

from engine.scene.nodepath import NodePath

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'


class Node(object):
    """
    Base class from which all Node Type classes should be subclassed.
    A Node object must at least provide size and name properties.
    """
    def __init__(self, node_path, name=None):
        # type: (NodePath, Optional[str]) -> None
        if not isinstance(node_path, NodePath):
            raise ValueError('invalid argument for node_path')
        self.__node_path__ = node_path
        self.__node_name__ = name or 'Unnamed Node'

    @property
    def size(self):
        # type: () -> Tuple[int, int]
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
    """
    A Node subclass, that holds one or more images, of which one can be
    rendered at a time. The ImageNode class
    """
    def __init__(self, node_path, name=None, image=None):
        super(ImageNode, self).__init__(node_path, name)
        self.__images__ = []            # type: List[str]
        self.__current_index__ = -1
        self.__asset_size__ = 0, 0
        self.__sprite__ = None
        if image is not None:
            self.add_image(image)

    def update(self, pos=None, scale=None, angle=None, depth=None):
        pass

    @property
    def size(self):
        # type: () -> Tuple[int, int]
        if self.__sprite__ is None:
            return 0, 0
        return self.sprite.area

    @property
    def sprite(self):
        # type: () -> TextureSprite
        if self.__sprite__ is None:
            raise ValueError('No sprite loaded')
        return self.__sprite__

    @sprite.setter
    def sprite(self, value):
        # type: (TextureSprite) -> None
        if isinstance(value, TextureSprite):
            self.__sprite__ = value
        else:
            raise TypeError('expected type sdl2.ext.Sprite')

    def show(self, item=None):
        # type: (Optional[int]) -> None
        """
        Loads the first image or optionally at the image with index `item`
        """
        item = item or 0
        if not (-1 < item < len(self.__images__)):
            raise IndexError('invalid index')
        if not self.__images__:
            raise ValueError('ImageNode contains no image(s)')
        if item != self.__current_index__:
            self.__current_index__ = item or 0
            self.update_sprite()

    def update_sprite(self):
        """
        Updates the sprite using relative position, angle and scale retrieved
        from the connected NodePath
        """
        if not self.__images__:
            raise ValueError('cannot update, no images added')
        self.sprite = self.node_path.sprite_loader.load_image(
            self.__images__[self.__current_index__],
            self.node_path.relative_scale
        )
        if self.node_path.relative_angle:
            self.sprite.angle = self.node_path.relative_angle
        pos = (
                self.node_path.relative_position
                * self.node_path.asset_pixel_ratio
        )
        self.sprite.position = tuple(pos)

    def add_image(self, image):
        # type: (str) -> None
        if os.path.isfile(image):
            img_size = Image.open(image).size
            if self.__images__ and img_size != self.__asset_size__:
                raise ValueError('All images in a ImageNode must be of the '
                                 'same exact size')
            self.__asset_size__ = img_size
            self.__images__.append(image)
        else:
            raise FileNotFoundError(f'unable to locate "{image}"')
