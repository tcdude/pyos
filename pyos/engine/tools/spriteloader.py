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
from typing import Optional

from sdl2.ext import SpriteFactory

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'


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
    def __init__(self, factory, asset_dir, cache_dir=None):
        # type: (SpriteFactory, str, Optional[str]) -> None
        if not isinstance(factory, SpriteFactory):
            raise TypeError('expected sdl2.ext.SpriteFactory for factory')
        if not os.path.isdir(asset_dir):
            raise NotADirectoryError(f'Invalid asset_dir')
        self.factory = factory
        self.asset_dir = asset_dir
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), 'cache')
        if not os.path.isdir(self.cache_dir):
            os.makedirs(self.cache_dir)
        self.__assets__ = {}
        self.__cache__ = {}
        self.refresh_assets()

    def refresh_assets(self):
        pass

    def load_image(self, asset_path, scale=1.0):
        pass
