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
import glob
import hashlib
import os
from typing import Optional
from typing import Tuple
from typing import Union

from PIL import Image
from sdl2.ext import SpriteFactory
from sdl2.ext import TextureSprite

from engine.tools import Point

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'

SCALE = Union[float, Tuple[float, float]]


class SpriteLoader(object):
    """
    Provides `load_*` methods that return Sprite objects of (cached) images
    and a method to compose/flatten multiple images into a single one.
    Automatically caches scaled and/or composed images on first load to reduce
    subsequent load time.

    Requires a SpriteFactory, a valid path to the asset directory and optionally
    the cache directory can be specified, otherwise a 'cache' directory,
    relative to `os.getcwd()` will be used. The cache_dir will be created if
    absent on init.
    """
    def __init__(
            self,
            factory,                    # type: SpriteFactory
            asset_dir,                  # type: str
            cache_dir=None,             # type: Optional[str]
            resize_type=Image.BICUBIC   # type: Optional[int]
    ):
        # type: (...) -> None
        if not isinstance(factory, SpriteFactory):
            raise TypeError('expected sdl2.ext.SpriteFactory for factory')
        if not os.path.isdir(asset_dir):
            raise NotADirectoryError(f'Invalid asset_dir')
        self.factory = factory
        self.asset_dir = asset_dir
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), 'cache')
        if not os.path.isdir(self.cache_dir):
            os.makedirs(self.cache_dir)
        self.resize_type = resize_type
        self.__assets__ = {}
        self.refresh_assets()

    def refresh_assets(self):
        paths = glob.glob(self.asset_dir + '/**/*.*')
        paths = [
            s[s.find(self.asset_dir) + len(self.asset_dir):] for s in paths
        ]
        if paths and paths[0].startswith('/'):
            paths = [s[1:] for s in paths]
        self.__assets__ = {}
        for k in paths:
            self.__assets__[k] = Asset(k, self)

    def load_image(self, asset_path, scale=1.0):
        # type: (str, Optional[SCALE]) -> TextureSprite
        return self.factory.from_image(self.__assets__[asset_path][scale])

    def load_composed_image(self, images):
        pass

    def empty_cache(self):
        for asset in self.__assets__.values():
            asset.empty_cache()


class Asset(object):
    def __init__(self, relative_path, parent):
        # type: (str, SpriteLoader) -> None
        self.relative_path = relative_path
        cache_name = hashlib.sha3_224(relative_path.encode()).hexdigest()
        self.cache_sub_dir = os.path.join(parent.cache_dir, cache_name[:2])
        self.cache_prefix = cache_name[2:]
        self.cache_suffix = '.' + relative_path.split('.')[-1]
        self.abs_path = os.path.join(parent.asset_dir, relative_path)
        self.__img_size__ = Point(Image.open(self.abs_path).size)
        self.__cached_items__ = {}
        self.parent = parent
        self.refresh_cached()

    def refresh_cached(self):
        self.__cached_items__ = {}
        files = glob.glob(self.cache_sub_dir + f'/{self.cache_prefix}*')
        for file in files:
            res = file.split('.')[-2][-10:]
            res = int(res[:5]), int(res[5:])
            self.__cached_items__[res] = file

    @property
    def size(self):
        return self.__img_size__

    def __getitem__(self, item):
        # type: (SCALE) -> str
        if isinstance(item, float):
            k = tuple((self.size * item).asint(True))
        elif isinstance(item, tuple) and len(item) == 2 and \
                isinstance(item[0], float) and isinstance(item[1], float):
            k = tuple(
                Point(self.size.x * item[0], self.size.y * item[1]).asint(True)
            )
        else:
            raise TypeError('expected type Union[float, Tuple[float, float]]')
        if k not in self.__cached_items__:
            self.cache(k)
        return self.__cached_items__[k]

    def cache(self, k):
        if not os.path.isdir(self.cache_sub_dir):
            os.makedirs(self.cache_sub_dir)
        fname = f'{self.cache_prefix}{k[0]:05d}{k[1]:05d}{self.cache_suffix}'
        p = os.path.join(self.cache_sub_dir, fname)
        Image.open(self.abs_path).resize(k, self.parent.resize_type).save(p)
        self.__cached_items__[k] = p

    def empty_cache(self):
        for f in self.__cached_items__.values():
            os.remove(f)
        try:
            os.rmdir(self.cache_sub_dir)
        except OSError as err:
            if err.errno != 39:
                raise err
        self.__cached_items__ = {}
