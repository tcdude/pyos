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

import math
import os
import subprocess

from PIL import Image

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.1'

# DEBUG ONLY
subprocess.call(['rm', '-rf', 'assets/cache'])

# Global Constants
# Default Configuration
CONFIG = {
    'draw_one': True,
    'tap_move': True,
    'auto_foundation': True,
    'left_handed': False,
}

# Paths
ASSETDIR = os.path.join(os.getcwd(), 'assets')
CACHEDIR = os.path.join(ASSETDIR, 'cache')
if not os.path.isdir(CACHEDIR):
    os.mkdir(CACHEDIR)
CONFIGFILE = os.path.join(CACHEDIR, 'config.bin')
BACKGROUND = os.path.join(ASSETDIR, 'images/bg.png')
CARDBACK = os.path.join(ASSETDIR, 'images/card_back.png')
COLORS = tuple('dchs')
DENOMINATIONS = tuple('a23456789') + ('10',) + tuple('jqk')
CARDS = {
    (c, d): os.path.join(
        ASSETDIR, 'images/{}{}.png'.format(COLORS[c], DENOMINATIONS[d])
    )
    for c in range(4) for d in range(13)
}
FOUNDATION = os.path.join(ASSETDIR, 'images/f_empty.png')
STACK = os.path.join(ASSETDIR, 'images/s_empty.png')
TABLEAU = os.path.join(ASSETDIR, 'images/t_empty.png')
WASTE = os.path.join(ASSETDIR, 'images/w_empty.png')

# Visual / Text
APPNAME = 'Adfree Simple Solitaire'
RATIO = (7.5, 4.7)
TOP_BAR = (0.96, 0.078125)
BOTTOM_BAR = (0.96, 0.08125)
TABLEAU_SPACING = 0.028125
COL_SPACING = 0.5 / 7.5 / 8
ROW_SPACING = 0.0125  # % of y resolution between stacked cards


# Helper Methods
def get_scale(screen_size, ratio, orig=CARDS[(0, 0)]):
    """Returns image scale to be applied in respect to screen size"""
    img = Image.open(orig)
    rx = (float(screen_size[0]) / ratio[0]) / img.size[0]
    ry = (float(screen_size[1]) / ratio[1]) / img.size[1]
    if rx < ry:     # Scale by X
        r = rx
    else:           # Scale by Y
        r = ry
    return int(round(img.size[0] * r, 0)), int(round(img.size[1] * r, 0))


def get_cards(screen_size, ratio=(7.5, 4.7)):
    """Returns a dict of cards and their image paths."""
    if not os.path.isdir(CACHEDIR):
        os.mkdir(CACHEDIR)
    x, y = get_scale(screen_size, ratio)
    cards = {}
    for c, d in CARDS:
        p = os.path.join(
            CACHEDIR,
            '{:04d}{:04d}{}{:02d}.bmp'.format(x, y, c, d)
        )
        cards[(c, d)] = p
        if not os.path.isfile(p):
            Image.open(CARDS[(c, d)]).resize((x, y), Image.BICUBIC).save(p)
    p = os.path.join(CACHEDIR, '{:04d}{:04d}cb.bmp'.format(x, y))
    cards[(-1, -1)] = p
    if not os.path.isfile(p):
        Image.open(CARDBACK).resize((x, y), Image.BICUBIC).save(p)
    return cards


def get_empty(screen_size, ratio=(7.5, 4.7)):
    """Returns a dict of the 4 placeholders"""
    x, y = get_scale(screen_size, ratio, FOUNDATION)
    d = {}
    for e in (STACK, WASTE, FOUNDATION, TABLEAU):
        f = os.path.split(e)[1]
        p = os.path.join(
            CACHEDIR,
            '{}{:04d}{:04d}.png'.format(f[0], x, y)
        )
        Image.open(e).resize((x, y), Image.BICUBIC).save(p)
        d[f[0]] = p
    return d


def get_table(screen_size, ratio=(7.5, 4.7), left_handed=False):
    """Returns the path of the table background image. Generates it if absent"""
    p = "pl" if left_handed else "pr"
    p += f'{screen_size[0]:04d}{screen_size[1]:04d}.bmp'
    p = os.path.join(CACHEDIR, p)
    if not os.path.isfile(p):
        cx, cy = get_scale(screen_size, ratio)
        empty = get_empty(screen_size, ratio)
        img = Image.new('RGBA', screen_size)
        placeholder = {
            k: Image.open(empty[k])
            for k in empty
        }
        bg = Image.open(BACKGROUND)
        for x in range(int(math.ceil(screen_size[0] / 512))):
            for y in range(int(math.ceil(screen_size[1] / 512))):
                img.paste(bg, (x * 512, y * 512))
        col = int(screen_size[0] * COL_SPACING)
        y_start = int(screen_size[1] * TOP_BAR[1])

        # Foundation
        r = range(6, 2, -1) if left_handed else range(4)
        for x in r:
            img.paste(
                placeholder['f'],
                (col + x * (cx + col), y_start),
                placeholder['f']
            )

        # Waste
        img.paste(
            placeholder['w'],
            (col + (1 if left_handed else 5) * (cx + col), y_start),
            placeholder['w']
        )

        # Stack
        img.paste(
            placeholder['s'],
            (col + (0 if left_handed else 6) * (cx + col), y_start),
            placeholder['s']
        )

        # Tableau
        y_start = y_start + cy + int(screen_size[1] * TABLEAU_SPACING)
        for x in range(7):
            img.paste(
                placeholder['t'],
                (col + x * (cx + col), y_start),
                placeholder['t']
            )
        img.save(p)
    return p
