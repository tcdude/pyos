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

import ctypes
import logging
import sys
import time
import traceback

import sdl2
import sdl2.ext

from engine.eventhandler import EventHandler
from engine.interval import PositionInterval
from engine.render import HWRenderer
from engine.taskmanager import TaskManager
from engine.tools import load_sprite
from engine.tools import nop
from engine.tools import toast
from engine.vector import Point

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.1'

ISANDROID = False
try:
    import android
    ISANDROID = True
    from android import hide_loading_screen
except ImportError:
    traceback.print_exc(file=sys.stdout)
    hide_loading_screen = nop


class App(object):
    def __init__(self, window_title='Unnamed'):
        self.__taskmgr__ = TaskManager()
        self.__event_handler__ = EventHandler()
        self.__taskmgr__.add_task('___EVENT_HANDLER___', self.__event_handler__)
        # noinspection PyTypeChecker
        self.__font_manager__ = None  # type: sdl2.ext.FontManager
        self.__world__ = sdl2.ext.World()
        self.__renderer__ = None
        self.__factory__ = None
        self.__window__ = None
        self.__window_title__ = window_title
        self.__screen_size__ = (0, 0)
        self.__running__ = False
        self.__mouse_pos__ = Point()
        self.__taskmgr__.add_task('___MOUSE_WATCHER___', self.__update_mouse__)
        self.__sequences__ = {}
        self.__anim_callbacks__ = {}
        self.__taskmgr__.add_task('___ANIMATION___', self.__animation__)
        self.__frames__ = 0
        self.__fps__ = 0.0
        self.__init_sdl__()
        self.__clean_exit__ = False

    @property
    def isandroid(self):
        return ISANDROID

    @property
    def world(self):
        return self.__world__

    # noinspection PyUnusedLocal
    @property
    def event_handler(self, *args, **kwargs):
        return self.__event_handler__

    @property
    def task_manager(self):
        return self.__taskmgr__

    @property
    def window(self):
        return self.__window__

    @property
    def mouse_pos(self):
        return self.__mouse_pos__.asint()

    @property
    def screen_size(self):
        return self.__screen_size__

    def load_sprite(self, fpath):
        return load_sprite(self.__factory__, fpath)

    @staticmethod
    def toast(message):
        toast(message)

    def init_font_manager(
            self,
            font_path,
            alias=None,
            size=16,
            color=sdl2.ext.Color(),
            bg_color=sdl2.ext.Color(0, 0, 0, 0)):
        if self.__font_manager__ is not None:
            self.__font_manager__.close()
        self.__font_manager__ = sdl2.ext.FontManager(
            font_path,
            alias,
            size,
            color,
            bg_color
        )

    def add_font(self, font_path, alias=None, size=16):
        if self.__font_manager__ is None:
            raise ValueError('FontManager not initialized. Call '
                             'init_font_manager() method first')
        self.__font_manager__.add(font_path, alias, size)

    def text_sprite(
            self,
            text,
            alias=None,
            size=None,
            width=None,
            color=None,
            bg_color=None,
            **kwargs):
        if self.__font_manager__ is None:
            raise ValueError('FontManager not initialized. Call '
                             'init_font_manager() method first')
        surface = self.__font_manager__.render(
            text,
            alias,
            size,
            width,
            color,
            bg_color,
            **kwargs
        )
        return self.__factory__.from_surface(surface)

    # noinspection PyUnusedLocal
    def __update_mouse__(self, *args, **kwargs):
        if not self.__running__:
            return
        x, y = ctypes.c_int(0), ctypes.c_int(0)
        _ = sdl2.mouse.SDL_GetMouseState(ctypes.byref(x), ctypes.byref(y))
        self.__mouse_pos__.x, self.__mouse_pos__.y = x.value, y.value

    # noinspection PyUnusedLocal
    def __animation__(self, dt, *args, **kwargs):
        if not self.__running__ or not self.__sequences__:
            return
        for k in self.__sequences__:
            sequence = self.__sequences__[k]
            rt = sequence[0].step(dt)
            if rt > 0:
                continue
            while rt <= 0:
                sequence.pop(0)
                if len(sequence):
                    rt = sequence[0].step(dt)
                else:
                    break
        p = []
        e = []
        for k in self.__sequences__:
            if not self.__sequences__[k]:
                p.append(k)
                if k in self.__anim_callbacks__:
                    e.append(k)
        for k in p:
            self.__sequences__.pop(k)
        for k in e:
            f, args, kwargs = self.__anim_callbacks__.pop(k)
            f(*args, **kwargs)

    def position_sequence(
            self,
            entity,
            depth,
            sequence,
            callback=None,
            *args,
            **kwargs):
        seq = []
        for duration, start_pos, end_pos in sequence:
            seq.append(PositionInterval(
                entity,
                depth,
                duration,
                start_pos,
                end_pos
            ))
        # k = str(entity)
        k = str((entity, depth, sequence))
        if k in self.__sequences__:
            self.__sequences__[k] += seq
        else:
            self.__sequences__[k] = seq
        if callback is not None:
            self.__anim_callbacks__[k] = (callback, args, kwargs)

    def stop_all_position_sequences(self):
        for k in self.__anim_callbacks__:
            f, args, kwargs = self.__anim_callbacks__[k]
            f(*args, **kwargs)
        self.__sequences__ = {}
        self.__anim_callbacks__ = {}

    def run(self):
        try:
            self.__running__ = True
            st = time.perf_counter()
            while self.__running__:
                self.task_manager(st)
                self.world.process()
                self.__frames__ += 1
                nt = time.perf_counter()
                time.sleep(max(0.0, 1 / 60 - (nt - st)))
                st = nt
        finally:
            sdl2.ext.quit()
            self.__clean_exit__ = True

    # noinspection PyUnusedLocal
    def quit(self, blocking=True, event=None):
        self.__running__ = False
        if blocking:
            while not self.__clean_exit__:
                time.sleep(0.01)

    def __init_sdl__(self):
        sdl2.ext.init()
        if self.isandroid:
            dm = sdl2.SDL_DisplayMode()
            sdl2.SDL_GetCurrentDisplayMode(0, dm)
            self.__screen_size__ = (dm.w, dm.h)
            toast(f'Got Screen Resolution of {dm.w}x{dm.h}')
        else:
            self.__screen_size__ = (720, 1280)
        self.__window__ = sdl2.ext.Window(
            self.__window_title__,
            size=self.__screen_size__
        )
        self.__window__.show()
        self.__renderer__ = HWRenderer(self.window)
        if self.isandroid:
            hide_loading_screen()
        self.__factory__ = sdl2.ext.SpriteFactory(
            sdl2.ext.TEXTURE,
            renderer=self.__renderer__
        )
        self.world.add_system(self.__renderer__)

    def __del__(self):
        if not self.__clean_exit__:
            sdl2.ext.quit()
