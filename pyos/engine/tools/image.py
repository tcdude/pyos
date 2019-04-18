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

from PIL import Image

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'


def cache_image(fpath, scale, cache_dir, suffix=None):
    # type: (str, float, str, Optional[str]) -> str
    img = Image.open(fpath)
    x, y = img.size
    out_x, out_y = int(round(x * scale, 0)), int(round(y * scale, 0))
    fname = os.path.split(fpath)[1]
    out_path = os.path.join(cache_dir, f'{out_x:05d}{out_y:05d}{fname}')
    if suffix is not None:
        out_path += suffix
    if not os.path.isfile(out_path):
        img.resize((out_x, out_y), Image.BICUBIC).save(out_path)
    return out_path
