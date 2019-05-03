"""
Provides Node classes that can be used in the Scene Graph.
"""

import os
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from PIL import Image
import sdl2.ext

from . import nodepath

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


class Node(object):
    """
    Base class from which all Node Type classes should be subclassed.
    A Node object must at least provide size and name properties.
    """
    def __init__(self, node_path, name=None):
        # type: (nodepath.NodePath, Optional[str]) -> None
        if not isinstance(node_path, nodepath.NodePath):
            raise ValueError('invalid argument for node_path')
        self._node_path = node_path
        self._node_name = name or 'Unnamed Node'

    @property
    def size(self):
        # type: () -> Union[Tuple[int, int], None]
        """``Tuple[int, int]`` or ``None``"""
        return None

    @property
    def node_path(self):
        """``NodePath``"""
        return self._node_path

    @property
    def name(self):
        """``str``"""
        return self._node_name

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
        self._images = []            # type: List[str]
        self._current_index = -1
        self._asset_size = 0, 0
        self._sprite = None
        if image is not None:
            self.add_image(image)

    def update(self, pos=None, scale=None, angle=None, depth=None):
        pass

    @property
    def size(self):
        # type: () -> Tuple[int, int]
        """``Tuple[int, int]``"""
        if self._sprite is None:
            return 0, 0
        return self.sprite.area

    @property
    def sprite(self):
        # type: () -> sdl2.ext.TextureSprite
        """``sdl2.ext.TextureSprite``"""
        if self._sprite is None:
            raise ValueError('No sprite loaded')
        return self._sprite

    @sprite.setter
    def sprite(self, value):
        # type: (sdl2.ext.TextureSprite) -> None
        if isinstance(value, sdl2.ext.TextureSprite):
            self._sprite = value
        else:
            raise TypeError('expected type sdl2.ext.Sprite')

    def show(self, item=None):
        # type: (Optional[int]) -> None
        """
        Loads the first image or optionally at the image with index ``item``
        """
        item = item or 0
        if not (-1 < item < len(self._images)):
            raise IndexError('invalid index')
        if not self._images:
            raise ValueError('ImageNode contains no image(s)')
        if item != self._current_index:
            self._current_index = item or 0
            self.update_sprite()

    def update_sprite(self):
        """
        Updates the sprite using relative position, angle and scale retrieved
        from the connected NodePath
        """
        if not self._images:
            raise ValueError('cannot update, no images added')
        self.sprite = self.node_path.sprite_loader.load_image(
            self._images[self._current_index],
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
        # type: (str) -> int
        """
        Add an image to the ``ImageNode``.

        :param image: ``str`` -> the image path relative to the asset directory.
        :return: ``int``
        """
        if os.path.isfile(image):
            img_size = Image.open(image).size
            if self._images and img_size != self._asset_size:
                raise ValueError('All images in a ImageNode must be of the '
                                 'same exact size')
            self._asset_size = img_size
            self._images.append(image)
            return len(self._images) - 1
        else:
            raise FileNotFoundError(f'unable to locate "{image}"')
