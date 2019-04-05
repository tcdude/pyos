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

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'

import ctypes
import os
import random

from PIL import Image
import sdl2.ext
import sdl2

from engine.render import HWRenderer
from engine.tools import toast
from engine.tools import load_sprite
from engine.tools import nop

HAVE_ANDROID = False

try:
    from android import hide_loading_screen
    HAVE_ANDROID = True
except ImportError:
    hide_loading_screen = nop


ASSETDIR = os.path.join(os.getcwd(), 'assets')
CARDBACK = os.path.join(ASSETDIR, 'images/card_back.png')
COLORS = tuple('dchs')
DENOMINATIONS = tuple('a23456789') + ('10',) + tuple('jqk')
CARDS = {
    (c, d): os.path.join(
        ASSETDIR, 'images/{}{}.png'.format(COLORS[c], DENOMINATIONS[d])
    )
    for c in range(4) for d in range(13)
}


class Card(object):
    def __init__(self, value, suit, visible=False):
        self.value = value
        self.suit = suit
        self.visible = visible


class CardEntity(sdl2.ext.Entity):
    def __init__(self, world, sprite, value, suit, visible=False, x=0, y=0):
        self.__world__ = world
        self.sprite = sprite
        self.sprite.position = x, y
        self.card = Card(value, suit, visible)


def get_img_resolution(screen_size, ratio):
    img = Image.open(CARDS[(0, 0)])
    rx = (float(screen_size[0]) / ratio[0]) / img.size[0]
    ry = (float(screen_size[1]) / ratio[1]) / img.size[1]
    if rx < ry:     # Scale by X
        r = rx
    else:           # Scale by Y
        r = ry
    return int(round(img.size[0] * r, 0)), int(round(img.size[1] * r, 0))


def get_cards(screen_size, ratio=(7.5, 4.7)):
    cache_dir = os.path.join(ASSETDIR, 'cache')
    if not os.path.isdir(cache_dir):
        os.mkdir(cache_dir)
    x, y = get_img_resolution(screen_size, ratio)
    toast(f'Scaling Images to {x}x{y}px...')
    cards = {}
    for c, d in CARDS:
        p = os.path.join(
            cache_dir,
            '{:04d}{:04d}{}{:02d}.bmp'.format(x, y, c, d)
        )
        cards[(c, d)] = p
        if not os.path.isfile(p):
            Image.open(CARDS[(c, d)]).resize((x, y), Image.BICUBIC).save(p)
    p = os.path.join(cache_dir, '{:04d}{:04d}cb.bmp'.format(x, y))
    cards[(-1, -1)] = p
    if not os.path.isfile(p):
        Image.open(CARDBACK).resize((x, y), Image.BICUBIC).save(p)
    toast('All Images scaled!')
    return cards


def main():
    sdl2.ext.init()
    dm = sdl2.SDL_DisplayMode()
    sdl2.SDL_GetCurrentDisplayMode(0, dm)
    toast(f'Got screen resolution of {dm.w}x{dm.h}px')
    window = sdl2.ext.Window('AdFreeSolitaire', size=(dm.w, dm.h))
    window.show()
    sw, sh = window.size  # dm.w, dm.h

    cards = get_cards((sw, sh))
    world = sdl2.ext.World()
    if HAVE_ANDROID:
        hide_loading_screen()

    # spriterenderer = SoftwareRenderer(window)
    spriterenderer = HWRenderer(window)
    world.add_system(spriterenderer)

    # factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
    factory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=spriterenderer)
    c = 3
    d = 5
    sprite = factory.from_surface(sdl2.ext.load_image(cards[(c, d)], 'SDL'))
    back = factory.from_surface(sdl2.ext.load_image(cards[(-1, -1)], 'SDL'))
    cardf = CardEntity(world, sprite, 2, 0, True, 10, 300)
    cardf.sprite.depth = 10
    cardback = CardEntity(world, back, 2, 0, True, 10, 300)
    cardback.sprite.depth = 1
    ph = [load_sprite(factory, cards[(-1, -1)]) for _ in range(7)]
    row = [
        CardEntity(
            world,
            s,
            -1,
            -1,
            x=sw - int(sw/7.5*(i+1) - 0.5 / 7),
            y=10
        ) for i, s in enumerate(ph)
    ]
    for i in row:
        i.sprite.depth = 1

    bg = os.path.join(ASSETDIR, 'images/bg.png')
    Image.open(bg).save(bg[:-4] + '.bmp')
    bg = bg[:-4] + '.bmp'
    bgs = [
        CardEntity(
            world,
            load_sprite(factory, bg),
            -1,
            -1,
            x=x * 512,
            y=y * 512
        ) for x in range(sw // 512 + 1) for y in range(sh // 512 + 1)
    ]
    for b in bgs:
        b.sprite.depth = 0
    running = True
    while running:
        x, y = ctypes.c_int(0), ctypes.c_int(0)
        _ = sdl2.mouse.SDL_GetMouseState(ctypes.byref(x), ctypes.byref(y))
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
                break
            if event.type == sdl2.SDL_MOUSEBUTTONUP:
                for card in row:
                    sx, sy = card.sprite.position
                    ex, ey = sx + card.sprite.size[0], sy + card.sprite.size[1]
                    if sx <= x.value <= ex and sy <= y.value <= ey:
                        if card.card.visible:
                            card.sprite = load_sprite(factory, cards[(-1, -1)])
                        else:
                            card.sprite = load_sprite(factory, cards[(
                                random.randrange(4),
                                random.randrange(13),
                            )])
                        card.card.visible = not card.card.visible
                        card.sprite.position = sx, sy
                        card.sprite.depth = 10
            if event.type == sdl2.SDL_KEYUP:  # IS_ANDROID
                print(event.key.keysym.sym)
                if event.key.keysym.sym in (sdl2.SDLK_AC_BACK, 27):
                    running = False
                    break
            if event.type == sdl2.SDL_MOUSEWHEEL:
                if event.wheel.y > 0:
                    d = (d + 1) % 13
                    c = c if d else (c + 1) % 4
                else:
                    d = (d - 1) % 13
                    c = c if d < 12 else (c - 1) % 4
                cardf.sprite = load_sprite(factory, cards[(c, d)])
                cardf.sprite.depth = 10 if cardf.card.visible else 1
        newx, newy = (
            x.value - sprite.size[0] // 2,
            y.value - sprite.size[1] // 2
        )
        cardf.sprite.position = (newx, newy)
        cardback.sprite.position = (newx, newy)

        world.process()
        # spriterenderer.render(sprite)
        # window.refresh()

    # processor = sdl2.ext.TestEventProcessor()
    # processor.run(window)

    sdl2.ext.quit()


if __name__ == '__main__':
    main()
