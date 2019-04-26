"""
Provides the App class to handle everything related to execution of an App.
"""

import ctypes
import time
from typing import Iterable
from typing import Optional
from typing import Tuple
from typing import Union

import sdl2
import sdl2.ext

from . import eventhandler
from . import interval
from . import render
from .scene import nodepath
from . import taskmanager
from . import tools
from .tools import vector

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

FRAME_TIME = 1 / 60

ISANDROID = False
try:
    import android
    ISANDROID = True
except ImportError:
    class Android(object):
        def remove_presplash(self):
            pass
    android = Android()


class App(object):
    # noinspection PyUnresolvedReferences
    """
        Base class that handles everything necessary to run an App.

        :param window_title: Optional str -> Window Title

        Example Usage:

        >>> class MyApp(App):
        ...    def __init__(self):
        ...         super(MyApp, self).__init__('My App Title')
        ...
        >>> MyApp().run()  # Opens the App and runs, until the App is closed.

        Todo:
            * Replace PySDL2 Component System with SceneGraph
        """
    def __init__(self, window_title='stupyd engine'):
        self.__taskmgr__ = taskmanager.TaskManager()
        self.__event_handler__ = eventhandler.EventHandler()
        self.__taskmgr__.add_task('___EVENT_HANDLER___', self.__event_handler__)
        self.__font_manager__ = None  # type: Union[sdl2.ext.FontManager, None]
        self.__world__ = sdl2.ext.World()
        self.__root__ = nodepath.NodePath('RootNodePath')
        self.__renderer__ = None
        self.__factory__ = None
        self.__window__ = None
        self.__window_title__ = window_title
        self.__screen_size__ = (0, 0)
        self.__running__ = False
        self.__mouse_pos__ = vector.Point()
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
        # type: () -> bool
        """``bool`` -> ``True`` if platform is android, otherwise ``False``."""
        return ISANDROID

    @property
    def world(self):
        # type: () -> sdl2.ext.World
        """``sdl2.ext.World``"""
        return self.__world__

    @property
    def renderer(self):
        # type: () -> sdl2.ext.TextureSpriteRenderSystem
        """``sdl2.ext.TextureSpriteRenderSystem``"""
        return self.__renderer__

    # noinspection PyUnusedLocal
    @property
    def event_handler(self, *args, **kwargs):
        # type: (...) -> eventhandler.EventHandler
        """``EventHandler``"""
        return self.__event_handler__

    @property
    def task_manager(self):
        # type: () -> taskmanager.TaskManager
        """``TaskManager``"""
        return self.__taskmgr__

    @property
    def window(self):
        # type: () -> sdl2.ext.Window
        """``sdl2.ext.Window``"""
        return self.__window__

    @property
    def mouse_pos(self):
        # type: () -> vector.Point
        """``Point`` -> current mouse position (=last touch location)"""
        return self.__mouse_pos__.asint()

    @property
    def screen_size(self):
        # type: () -> Tuple[int, int]
        """``Tuple[int, int]``"""
        return self.__screen_size__

    def load_sprite(self, fpath):
        # type: (str) -> sdl2.ext.TextureSprite
        """
        Load a sprite from ``fpath``.
        :param fpath: ``str`` -> path of an image file.
        :return: ``sdl2.ext.TextureSprite``
        """
        return tools.load_sprite(self.__factory__, fpath)

    def entity_in_sequences(self, entity):
        # type: (sdl2.ext.Entity) -> bool
        """
        Returns ``True`` when ``entity`` is currently in a sequence.

        :param entity: ``sdl2.ext.Entity``
        :return: ``bool``
        """
        return True if str(entity) in self.__sequences__ else False

    def toast(self, message):
        # type: (str) -> None
        """
        If on android, shows ``message`` as a `toast` on screen.

        :param message: ``str`` -> the message to display.
        """
        if self.isandroid:
            tools.toast(message)

    def init_font_manager(
            self,
            font_path,                          # type: str
            alias=None,                         # type: Optional[str]
            size=16,                            # type: Optional[int]
            color=sdl2.ext.Color(),             # type: Optional[sdl2.ext.Color]
            bgcolor=sdl2.ext.Color(0, 0, 0, 0)  # type: Optional[sdl2.ext.Color]
    ):
        # type: (...) -> None
        """
        Initializes the ``sdl2.ext.FontManager``.

        :param font_path: ``str`` -> Path to the default font.
        :param alias: Optional ``str`` -> alias of the font.
        :param size: Optional ``int`` -> font size
        :param color: Optional ``sdl2.ext.Color`` -> foreground color
        :param bgcolor: Optional ``sdl2.ext.Color`` -> background color
        """
        if self.__font_manager__ is not None:
            self.__font_manager__.close()
        self.__font_manager__ = sdl2.ext.FontManager(
            font_path,
            alias,
            size,
            color,
            bgcolor
        )

    def add_font(self, font_path, alias=None, size=16):
        """
        Add a font to the ``sdl2.ext.FontManager``.

        :param font_path: ``str`` -> Path to the default font.
        :param alias: Optional ``str`` -> alias of the font.
        :param size: Optional ``int`` -> font size
        """
        if self.__font_manager__ is None:
            raise ValueError('FontManager not initialized. Call '
                             'init_font_manager() method first')
        self.__font_manager__.add(font_path, alias, size)

    def text_sprite(
            self,
            text,               # type: str
            alias=None,         # type: Optional[str]
            size=None,          # type: Optional[int]
            width=None,         # type: Optional[int]
            color=None,         # type: Optional[sdl2.ext.Color]
            bg_color=None,      # type: Optional[sdl2.ext.Color]
            **kwargs
    ):
        # type: (...) -> sdl2.ext.TextureSprite
        """
        Load text as a Sprite.

        :param text: ``str`` -> the text to load.
        :param alias: Optional ``str`` -> the alias of the font to use.
        :param size: Optional ``int`` -> the font size.
        :param width: Optional ``int`` -> the width used for word wrap.
        :param color: Optional ``sdl2.ext.Color`` -> the foreground color
        :param bg_color: Optional ``sdl2.ext.Color`` -> the background color
        :param kwargs: additional keyword arguments, passed into
            ``sdl2.ext.FontManager.render()``
        :return: ``sdl2.ext.TextureSprite``
        """
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
        sprite = self.__factory__.from_surface(surface)
        sdl2.SDL_FreeSurface(surface)
        return sprite

    # noinspection PyUnusedLocal
    def __update_mouse__(self, *args, **kwargs):
        # type: (...) -> None
        """Updates ``App.mouse_pos``."""
        if not self.__running__:
            return
        x, y = ctypes.c_int(0), ctypes.c_int(0)
        _ = sdl2.mouse.SDL_GetMouseState(ctypes.byref(x), ctypes.byref(y))
        self.__mouse_pos__.x, self.__mouse_pos__.y = x.value, y.value

    # noinspection PyUnusedLocal
    def __animation__(self, dt, *args, **kwargs):
        # type: (float, ..., ...) -> None
        """Animation Task."""
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
            entity,             # type: sdl2.ext.Entity
            depth,              # type: int
            sequence,           # type: Iterable[Tuple[float, vector.Point, vector.Point]]
            callback=None,      # type: Optional[callable]
            *args,
            **kwargs
    ):
        # type: (...) -> None
        """
        Add a sequence of PositionInterval for ``entity``.

        :param entity: ``sdl2.ext.Entity``
        :param depth: ``int`` -> depth during the sequence.
        :param sequence: ``Iterable[Tuple[float, Point, Point]]`` -> iterable of
            3-tuple containing (``duration``, ``start_pos``, ``end_pos``).
        :param callback: Optional ``callable`` -> callable to execute after the
            sequence is completed.
        :param args: Optional positional arguments to pass to ``callback``.
        :param kwargs: Optional keyword arguments to pass to ``callback``.
        """
        seq = []
        for duration, start_pos, end_pos in sequence:
            seq.append(interval.PositionInterval(
                entity,
                depth,
                duration,
                start_pos,
                end_pos
            ))
        k = str(entity)
        if k in self.__sequences__:
            if k in self.__anim_callbacks__:
                f, args, kwargs = self.__anim_callbacks__[k]
                f(*args, **kwargs)
        self.__sequences__[k] = seq
        if callback is not None:
            self.__anim_callbacks__[k] = (callback, args, kwargs)

    def stop_all_position_sequences(self):
        """Stops all position sequences and calls the respective callbacks."""
        for k in self.__anim_callbacks__:
            f, args, kwargs = self.__anim_callbacks__[k]
            f(*args, **kwargs)
        self.__sequences__ = {}
        self.__anim_callbacks__ = {}

    def run(self):
        """
        Run the main loop until ``App.quit()`` gets called.

        .. warning::
            Make sure to call ``super(YourClassName, self).run()`` if you
            override this method!!!
        """
        try:
            self.__running__ = True
            st = time.perf_counter()
            while self.__running__:
                self.task_manager(st)
                self.world.process()
                self.__frames__ += 1
                nt = time.perf_counter()
                time.sleep(max(0.0, FRAME_TIME - (nt - st)))
                st = nt
        except (KeyboardInterrupt, SystemExit):
            self.quit(blocking=False)
        finally:
            sdl2.ext.quit()
            self.__clean_exit__ = True

    # noinspection PyUnusedLocal
    def quit(self, blocking=True, event=None):
        # type: (Optional[bool], Optional[sdl2.SDL_Event]) -> None
        """
        Exit the main loop and quit the app.

        :param blocking: Optional ``bool`` -> whether the method should wait
            until the App has quit.
        :param event: Optional ``sdl2.SDL_Event`` -> Unused, used to enable
            being executed by an event callback.

        .. warning::
            Do not override this method, override ``App.on_quit()`` instead!!!

        """
        if not self.__running__:
            return
        self.on_quit()
        self.__running__ = False
        if blocking:
            while not self.__clean_exit__:
                time.sleep(0.01)

    def on_quit(self):
        """
        Method to override to perform cleanup when ``App.quit()`` gets called.
        """
        pass

    def __init_sdl__(self):
        """Initializes SDL2."""
        sdl2.ext.init()
        if self.isandroid:
            dm = sdl2.SDL_DisplayMode()
            sdl2.SDL_GetCurrentDisplayMode(0, dm)
            self.__screen_size__ = (dm.w, dm.h)
            sdl2.ext.Window.DEFAULTFLAGS = sdl2.SDL_WINDOW_FULLSCREEN
        else:
            self.__screen_size__ = (720, 1280)
        self.__window__ = sdl2.ext.Window(
            self.__window_title__,
            size=self.__screen_size__
        )
        self.__window__.show()
        android.remove_presplash()
        self.__renderer__ = render.HWRenderer(self.window)
        self.__factory__ = sdl2.ext.SpriteFactory(
            sdl2.ext.TEXTURE,
            renderer=self.__renderer__
        )
        self.world.add_system(self.__renderer__)

    def __del__(self):
        """Make sure, ``sdl2.ext.quit()`` gets called latest on destruction."""
        if not self.__clean_exit__:
            sdl2.ext.quit()
