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
__version__ = '0.1'

import sdl2
import sdl2.ext

from engine.eventhandler import EventHandler
from engine.render import HWRenderer
from engine.tools import load_sprite
from engine.tools import toast
from engine.tools import nop

ISANDROID = False

try:
    from android import hide_loading_screen
    ISANDROID = True
except ImportError:
    hide_loading_screen = nop


class App(object):
    def __init__(self, window_title='Unnamed'):
        self.__event_handler__ = EventHandler()
        self.__world__ = sdl2.ext.World()
        self.__renderer__ = None
        self.__factory__ = None

        self.__window__ = None
        self.__window_title__ = window_title
        self.__screen_size__ = (0, 0)

        self.__running__ = False

    @property
    def isandroid(self):
        return ISANDROID

    @property
    def world(self):
        return self.__world__

    @property
    def event_handler(self):
        return self.__event_handler__

    @property
    def window(self):
        return self.__window__

    def load_sprite(self, fpath):
        return load_sprite(self.__factory__, fpath)

    @staticmethod
    def toast(message):
        toast(message)

    def run(self):
        self.__init_sdl__()
        self.__running__ = True
        while self.__running__:
            self.event_handler()
            self.world.process()
        sdl2.ext.quit()

    def __init_sdl__(self):
        sdl2.ext.init()
        dm = sdl2.SDL_DisplayMode()
        sdl2.SDL_GetCurrentDisplayMode(0, dm)
        self.__screen_size__ = (dm.w, dm.h)
        self.__window__ = sdl2.ext.Window(
            self.__window_title__,
            size=self.__screen_size__
        )
        self.__renderer__ = HWRenderer(self.window)
        if self.isandroid:
            hide_loading_screen()
        self.__factory__ = sdl2.ext.SpriteFactory(
            sdl2.ext.TEXTURE,
            renderer=self.__renderer__
        )
        self.world.add_system(self.__renderer__)
