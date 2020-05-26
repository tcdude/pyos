"""
Provides the CardMaker class to create the deck.
"""

from dataclasses import dataclass, field
import os
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont
from foolysh.tools import sdf

import common

__author__ = 'Tiziano Bettio'
__copyright__ = """
Copyright (c) 2020 Tiziano Bettio

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
__license__ = 'MIT'
__version__ = '0.3'


@dataclass
class Images:
    """Holds Image instances."""
    card: Image.Image = None
    sym: Dict[str, Dict[str, Image.Image]] = field(default_factory=dict)
    value: Dict[str, Dict[str, Image.Image]] = field(default_factory=dict)


@dataclass
class ImageInfo:
    """Holds information about the value and suit images."""
    symx: int = None
    symh: int = None
    symc: int = None
    vmaxw: int = None


class CardMaker:
    """
    Provides deck creation using suit symbols.

    Args:
        size: The size in pixels of a card.
        assetdir:
        outdir: The path to store the deck in.
    """
    def __init__(self, size: Tuple[int, int], assetdir: str, outdir: str
                 ) -> None:
        self._size: Tuple[int, int] = None
        self._margin: int = None
        self._imi = ImageInfo()
        self._assetdir = assetdir
        self._outdir = None
        self._im = Images()
        self.change_setup(size, outdir)

    def generate(self, left_handed: bool = False) -> None:
        """
        Generate a deck with the current size.

        Args:
            left_handed: whether to place value and suit on the top left or
                right.
        """
        prefix = 'l' if left_handed else 'r'
        center = ((self._size[0] - self._imi.symc) // 2,
                  self._size[1] - self._margin - self._imi.symc)

        def get_x(width):
            offset = (self._imi.vmaxw - width) // 2
            vleft = self._margin + offset
            vright = self._size[0] - width - self._margin - offset
            sright = self._size[0] - self._imi.symh - self._margin
            if left_handed:
                return vright, vleft
            return vleft, sright
        for suit in common.COLORS:
            for value in common.DENOMINATIONS:
                fpath = os.path.join(self._outdir, f'{prefix}{suit}{value}.png')
                if os.path.exists(fpath) \
                      and Image.open(fpath).size == self._size:
                    return
                card = Image.new('RGBA', self._size, (0, 0, 0, 0))
                card.alpha_composite(self._im.card)
                card.alpha_composite(self._im.sym[suit]['L'], center)
                symv = self._im.value['r' if suit in ('d', 'h') else 'b'][value]
                syms = self._im.sym[suit]['S']
                symx = self._im.sym[suit]['XS']
                for sym, posx in zip((symv, syms), get_x(symv.size[0])):
                    card.alpha_composite(sym, (posx, self._margin))
                    if sym == symv:
                        off = 0
                        if left_handed:
                            off = max(symx.size[0] - symv.size[0], 0)
                        card.alpha_composite(symx,
                                             (posx - off,
                                              self._margin
                                              + int(symv.size[1] * 1.1)))
                card.save(fpath)

    def change_setup(self, size: Tuple[int, int], outdir: str) -> None:
        """Change the card size and outdir."""
        if self._size == size and self._outdir == outdir:
            return
        self._outdir = outdir
        self._size = size
        os.makedirs(self._outdir, exist_ok=True)
        self._margin = int(min(size) * common.CARDCORNER + 0.5)
        border = int(min(size) * common.CARDBORDER + 0.5)
        self._im.card = sdf. \
            framed_box_im(*self._size, self._margin, border,
                          common.CARDBG_COLOR[:3], common.CARDBLACK,
                          multi_sampling=common.CARD_MULTISAMPLING,
                          alpha=common.CARDBG_COLOR[3])
        self._margin = self._margin // 2 + 1
        self._imi.symx = int(size[1] * common.CARDSYMHEIGHTXS + 0.5)
        self._imi.symh = int(size[1] * common.CARDSYMHEIGHT + 0.5)
        self._imi.symc = int(size[1] * common.CARDSYMCENTER + 0.5)
        self._im.sym.clear()
        for suit in common.COLORS:
            self._im.sym[suit] = {
                'XS': Image \
                    .open(os.path.join(self._assetdir, common.SUITSYM[suit])) \
                    .resize((self._imi.symh, self._imi.symh), Image.BICUBIC),
                'S': Image \
                    .open(os.path.join(self._assetdir, common.SUITSYM[suit])) \
                    .resize((self._imi.symh, self._imi.symh), Image.BICUBIC),
                'L': Image \
                    .open(os.path.join(self._assetdir, common.SUITSYM[suit])) \
                    .resize((self._imi.symc, self._imi.symc), Image.BICUBIC)}
        self._gen_values(self._imi.symh)

    def _gen_values(self, symh: int) -> None:
        self._im.value.clear()
        fnt = self._get_font(symh)
        self._imi.vmaxw = 0
        for col in ('r', 'b'):
            fill = common.CARDRED if col == 'r' else common.CARDBLACK
            self._im.value[col] = {}
            for value in common.DENOMINATIONS:
                txt = value.upper()
                left, top, right, bottom = fnt.getmask(txt).getbbox()
                pos = fnt.getoffset(txt)
                pos = -(left + pos[0]), -(top + pos[1])
                im_sz = right - left, bottom - top
                img = Image.new('RGBA', im_sz, (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                draw.text(pos, txt, fill=fill, font=fnt)
                self._im.value[col][value] = img
                self._imi.vmaxw = max(self._imi.vmaxw, img.size[0])

    def _get_font(self, symh: int) -> None:
        fntsz = symh
        fnth = 0
        fntpath = os.path.join(self._assetdir, common.CARDFONT)
        fnt = ImageFont.truetype(fntpath, fntsz)
        txt = ''.join(common.DENOMINATIONS)
        direction = 0
        search = True
        while search:
            _, top, _, bottom = fnt.getmask(txt).getbbox()
            fnth = bottom - top
            if fnth < symh:
                if direction >= 0:
                    direction = 1
                    fntsz += 1
                else:
                    search = False
            elif fnth > symh:
                if direction <= 0:
                    direction = -1
                    fntsz -= 1
                else:
                    fntsz -= 1
                    search = False
            else:
                break
            fnt = fnt.font_variant(size=fntsz)
        return fnt
