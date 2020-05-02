"""
Provides the base class for all states and all attributes/methods that are
shared with all the states.
"""

from dataclasses import dataclass
from typing import Tuple

from loguru import logger
import sdl2
import plyer

from foolysh import app
from foolysh.scene.node import Origin
from foolysh.ui import label

import common
import mpctrl
import mpdb
import stats
import rules

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
class MPSystems:
    """Holds multiplayer related systems."""
    ctrl: mpctrl.MPControl
    dbh: mpdb.MPDBHandler
    login: int = -1


class AppBase(app.App):
    """
    Serves as base for all states registered through multiple inheritance. All
    attributes, properties and methods that are shared across the app are
    defined in this class.
    """
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.statuslbl = label.Label(text='', **common.STATUS_TXT_KW)
        self.statuslbl.reparent_to(self.ui.center)
        self.statuslbl.origin = Origin.CENTER
        self.statuslbl.depth = 2000
        self.statuslbl.hide()

        self.layout_refresh = False
        self.need_new_game = False
        self.shuffler = rules.Shuffler()
        dtf = self.config.get('pyos', 'datafile',
                              fallback=common.DEFAULTCONFIG['pyos']['datafile'])
        self.stats = stats.Stats(dtf)
        self.config.save()
        self.stats.start_session()
        self.daydeal: Tuple[int, int] = None
        self.mps = MPSystems(mpctrl.MPControl(self.config),
                             mpdb.MPDBHandler(common.MPDATAFILE))
        self.login()
        self.__last_orientation: str = None
        self.__setup_events_tasks()
        logger.debug('AppBase initialized')

    def login(self) -> None:
        """Attempts to login to multiplayer."""
        if not self.mps.ctrl.noaccount:
            req = self.mps.ctrl.update_user_ranking()
            print(req)
            self.mps.ctrl.register_callback(req, self.__logincb)
            self.statuslbl.text = 'Login...'
            self.statuslbl.show()

    def __logincb(self, rescode: int) -> None:
        self.statuslbl.hide()
        self.mps.login = rescode
        if rescode:
            logger.warning(f'Login failed with rescode '
                           f'{mpctrl.RESTXT[rescode]}')
        else:
            logger.debug('Login successful')

    def __setup_events_tasks(self):
        """Setup Events and Tasks."""
        logger.debug('Setting up global events and tasks')
        self.event_handler.listen('quit', sdl2.SDL_QUIT, self.quit,
                                  blocking=False)
        self.event_handler.listen('android_back', sdl2.SDL_KEYUP, self.__back)
        self.task_manager.add_task('MPUPDATE', self.mps.ctrl.update, 0.1, False)
        if self.isandroid:
            plyer.gravity.enable()
            self.event_handler.listen('APP_TERMINATING',
                                      sdl2.SDL_APP_TERMINATING, self.quit,
                                      blocking=False)
            self.event_handler.listen('APP_WILLENTERBACKGROUND',
                                      sdl2.SDL_APP_WILLENTERBACKGROUND,
                                      self.__event_will_enter_bg)
            self.event_handler.listen('APP_DIDENTERBACKGROUND',
                                      sdl2.SDL_APP_DIDENTERBACKGROUND,
                                      self.__event_pause)
            self.event_handler.listen('APP_DIDENTERFOREGROUND',
                                      sdl2.SDL_APP_DIDENTERFOREGROUND,
                                      self.__event_resume)
            self.event_handler.listen('APP_LOWMEMORY', sdl2.SDL_APP_LOWMEMORY,
                                      self.__event_low_memory)
            self.task_manager.add_task('ORIENTATION', self.__orientation, 0.2,
                                       False)

    def __back(self, event):
        """Handles Android Back, Escape and Backspace Events"""
        if event.key.keysym.sym in (sdl2.SDLK_AC_BACK, 27):
            if self.active_state != 'main_menu':
                self.fsm_back()
            else:
                self.quit(blocking=False)

    def __event_pause(self, event=None):
        """Called when the app enters background."""
        # pylint: disable=unused-argument
        logger.info('Paused app')
        self.request('app_base')
        self.stats.end_session()

    def __event_resume(self, event=None):
        """Called when the app enters background."""
        # pylint: disable=unused-argument
        logger.info('Resume app')
        self.request('main_menu')
        self.stats.start_session()

    def __event_will_enter_bg(self, event=None):
        """Called when the os announces that the app will enter background."""
        # pylint: disable=unused-argument
        logger.warning('Unhandled event APP_WILLENTERBACKGROUND!!!')
        self.request('app_base')

    @staticmethod
    def __event_low_memory(event=None):
        """Called when the os announces low memory."""
        # pylint: disable=unused-argument
        logger.warning('Unhandled event APP_LOWMEMORY!!!')

    def __orientation(self):
        """Handles orientation change."""
        orientation = self.config.get('pyos', 'orientation', fallback='auto')
        if orientation == 'auto':
            plyer.orientation.set_sensor()
            return
        gravity = plyer.gravity.gravity
        if abs(gravity[0]) > abs(gravity[1]):
            if gravity[0] > 0:
                new_orientation = 'landscape'
            else:
                new_orientation = 'landscape_reversed'
        else:
            if gravity[1] > 0:
                new_orientation = 'portrait'
            else:
                new_orientation = 'portrait_reversed'
        if new_orientation != self.__last_orientation:
            self.__last_orientation = new_orientation
            logger.info(f'Updating orientation to "{new_orientation}"')
            if new_orientation == 'landscape' and orientation == 'landscape':
                plyer.orientation.set_landscape()
            elif new_orientation == 'landscape_reversed' \
                  and orientation == 'landscape':
                plyer.orientation.set_landscape(reverse=True)
            elif new_orientation == 'portrait' and orientation == 'portrait':
                plyer.orientation.set_portrait()
            elif new_orientation == 'portrait_reversed' \
                  and orientation == 'portrait':
                plyer.orientation.set_portrait(reverse=True)


    def on_quit(self):
        """Overridden on_quit event to make sure the state is saved."""
        logger.info('Saving state and quitting pyos')
        self.request('app_base')
        if self.isandroid:
            plyer.gravity.disable()
        self.stats.end_session()
        self.stats.close()
        self.mps.ctrl.stop()
        super().on_quit()

    def enter_app_base(self):
        """Stub to enable this to become a state."""

    def exit_app_base(self):
        """Stub to enable this to become a state."""
