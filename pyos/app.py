"""
Provides the base class for all states and all attributes/methods that are
shared with all the states.
"""

from dataclasses import dataclass, field
import glob
import os
import shutil
import struct
import time
from typing import Any, Callable, Dict, Tuple

from loguru import logger
import sdl2
import plyer

from foolysh import app
from foolysh.scene import node
from foolysh.scene.node import Origin
from foolysh.ui import label

import cardmaker
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

CBDictT = Dict[str, Tuple[Callable, Tuple[Any, ...], Dict[str, Any]]]


@dataclass
class MPSystems:
    """Holds multiplayer related systems."""
    ctrl: mpctrl.MPControl
    dbh: mpdb.MPDBHandler
    login: int = -1
    last_check: int = 0
    conncheck: bool = True
    notification_callback: CBDictT = field(default_factory=dict)


@dataclass
class State:
    """Holds various state attributes."""
    statefile: str
    daydeal: Tuple[int, int] = None
    challenge: int = -1
    layout_refresh: bool = False
    need_new_game: bool = True
    foundation_moves: int = 0

    def load(self) -> None:
        """Attempts to load the state from disk."""
        try:
            with open(self.statefile, 'rb') as fhandler:
                data = fhandler.read()
        except FileNotFoundError:
            logger.warning('State file does not exist')
            return
        try:
            seed, draw, chg, ref, nng = struct.unpack('<Bii??', data[:11])
        except struct.error as err:
            logger.error(f'Unable to unpack data {err}')
            return
        # Added in 0.3.50 as cheat prevention
        if len(data) > 11:
            try:
                foundation_moves = struct.unpack('<B', data[11:])
            except struct.error as err:
                logger.error(f'Unable to unpack data {err}')
                return
            else:
                self.foundation_moves = foundation_moves[0]
        if seed == draw == 0:
            self.daydeal = None
        else:
            self.daydeal = seed, draw
        self.challenge = chg
        self.layout_refresh = ref
        self.need_new_game = nng

    def save(self) -> None:
        """Saves the current state to the statefile."""
        daydeal = self.daydeal or (0, 0)
        with open(self.statefile, 'wb') as fhandler:
            try:
                fhandler.write(struct.pack('<Bii??B', *daydeal, self.challenge,
                                           self.layout_refresh,
                                           self.need_new_game,
                                           self.foundation_moves))
            except struct.error as err:
                data = (*daydeal, self.challenge, self.layout_refresh,
                        self.need_new_game, self.foundation_moves)
                logger.error(f'Unable to pack data={data} {err}')


@dataclass
class Systems:
    """Holds global systems"""
    stats: stats.Stats
    shuffler: rules.Shuffler


@dataclass
class GlobalNodes:
    """Holds globally accessible Nodes."""
    statuslbl: label.Label = None
    mpstatus: label.Label = None
    seed: node.TextNode = None

    def show_status(self, text: str) -> None:
        """Show the statuslbl with the given text."""
        self.statuslbl.text = text
        self.statuslbl.show()

    def hide_status(self, *unused_args, **unused_kwargs) -> None:
        """Hides the statuslbl."""
        self.statuslbl.hide()

    def set_mpstatus(self, text: str) -> None:
        """Updates the mpstatus text."""
        self.mpstatus.text = text
        self.mpstatus.show()

    def set_seed(self, seed: int, dealtype: str = '') -> None:
        """Sets the random seed."""
        if self.seed is None:
            logger.warning('Seed node not initialized yet')
            return
        txt = f'Deal {seed:010d}'
        if dealtype:
            self.seed.text = ' '.join([dealtype, txt])
        else:
            self.seed.text = txt


class AppBase(app.App):
    """
    Serves as base for all states registered through multiple inheritance. All
    attributes, properties and methods that are shared across the app are
    defined in this class.
    """
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.global_nodes = GlobalNodes()
        self.global_nodes.statuslbl = label \
            .Label(text='', parent=self.ui.top_center, **common.STATUS_TXT_KW)
        self.global_nodes.statuslbl.origin = Origin.CENTER
        self.global_nodes.statuslbl.depth = 2000
        self.global_nodes.statuslbl.hide()
        self.global_nodes.mpstatus = label \
            .Label(text='Not logged in', parent=self.ui.bottom_center,
                   **common.MPSTATUS_TXT_KW)
        self.global_nodes.mpstatus.origin = Origin.CENTER
        self.global_nodes.mpstatus.depth = 2000

        dtf = self.config.get('pyos', 'datafile',
                              fallback=common.DEFAULTCONFIG['pyos']['datafile'])
        self.systems = Systems(stats.Stats(dtf), rules.Shuffler())
        path = os.path.join(self.config['base']['cache_dir'],
                            self.config['pyos']['app_state_file'])
        self.state = State(path)
        self.state.load()
        self.config.save()
        self.systems.stats.start_session()
        self.mps = MPSystems(mpctrl.MPControl(self.config),
                             mpdb.MPDBHandler(common.MPDATAFILE))
        self.mps.ctrl.start_service()
        self.login()
        self.__last_orientation: str = None
        self.__setup_events_tasks()
        self.update_cards()
        logger.debug('AppBase initialized')

    def login(self, txt: str = 'Connecting to server...') -> None:
        """Attempts to login to multiplayer."""
        if not self.mps.ctrl.noaccount:
            req = self.mps.ctrl.nop()
            self.mps.ctrl.register_callback(req, self.__logincb)
            self.global_nodes.show_status(txt)
        else:
            self.mps.ctrl.nop()

    def __logincb(self, rescode: int) -> None:
        self.global_nodes.hide_status()
        self.mps.login = rescode
        if rescode:
            txt = f'Error: {mpctrl.RESTXT[rescode]}'
            self.global_nodes.set_mpstatus(txt)
            logger.warning(txt)
        else:
            logger.debug('Login successful')
            user = self.config.get('mp', 'user')
            self.global_nodes.set_mpstatus(f'Logged in as {user}')
            self.__conn_check()

    def __setup_events_tasks(self):
        """Setup Events and Tasks."""
        logger.debug('Setting up global events and tasks')
        self.event_handler.listen('quit', sdl2.SDL_QUIT, self.quit,
                                  blocking=False)
        self.event_handler.listen('android_back', sdl2.SDL_KEYUP, self.__back)
        self.task_manager.add_task('MPUPDATE', self.mps.ctrl.update, 0, False)
        self.task_manager.add_task('CONNCHK', self.__conn_check, 10, False)
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

    def disable_connection_check(self) -> None:
        """Disable the connection check task."""
        self.task_manager['CONNCHK'].pause()
        self.task_manager['MPUPDATE'].delay = 5.0
        self.mps.conncheck = False

    def enable_connection_check(self) -> None:
        """Enable the connection check task."""
        if self.mps.conncheck:
            return
        self.task_manager['CONNCHK'].resume()
        self.task_manager['MPUPDATE'].delay = 0
        self.mps.conncheck = True

    def update_cards(self) -> None:
        """Makes sure all cards are loaded and present in the assetdir."""
        if not self.config.getboolean('pyos', 'readability'):
            return
        assetdir = self.config.get('base', 'asset_dir')
        cmk = cardmaker \
            .CardMaker(common.ORIGCARDSIZE, assetdir, common.SIMPLECARDS)
        cmk.generate(self.config.getboolean('pyos', 'left_handed',
                                            fallback=False))
        assetdir = os.path.join(assetdir, 'images')
        for i in glob.glob(common.SIMPLECARDS + '/*.png'):
            shutil.copy(i, assetdir)

    def __conn_check(self, force: bool = False) -> None:
        if self.active_state == 'game':
            return
        if time.time() - self.mps.last_check > 30 or force:
            req = self.mps.ctrl.sync_challenges()
            update_status = True
        else:
            req = self.mps.ctrl.nop()
            update_status = False
        self.mps.ctrl.register_callback(req, self.__conn_checkcb, update_status)

    def __conn_checkcb(self, rescode: int, update_status: bool) -> None:
        self.mps.login = rescode
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
            self.global_nodes.set_mpstatus('Not logged in')
        elif update_status:
            self.mps.last_check = time.time()
            cha = self.mps.dbh.challenge_actions
            fra = self.mps.dbh.friend_actions
            sym = common.bubble_number(cha + fra)
            user = self.config.get('mp', 'user')
            txt = user
            txt += f' {sym}' if sym else ''
            fnt = self.config.get('font', 'bold' if sym else 'normal')
            self.global_nodes.mpstatus.font = fnt
            self.global_nodes.set_mpstatus(f'Logged in as {txt}')
            for k in self.mps.notification_callback:
                callback, args, kwargs = self.mps.notification_callback[k]
                callback(cha, fra, *args, **kwargs)

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
        self.systems.stats.end_session()
        self.state.save()
        # self.mps.ctrl.stop()

    def __event_resume(self, event=None):
        """Called when the app enters background."""
        # pylint: disable=unused-argument
        logger.info('Resume app')
        self.login()
        self.request('main_menu')
        common.release_gamestate()
        self.systems.stats.start_session()

    def __event_will_enter_bg(self, event=None):
        """Called when the os announces that the app will enter background."""
        # pylint: disable=unused-argument
        logger.warning('Unhandled event APP_WILLENTERBACKGROUND!!!')
        self.request('app_base')

    def __event_low_memory(self, event=None):
        """Called when the os announces low memory."""
        # pylint: disable=unused-argument
        logger.warning('Unhandled event APP_LOWMEMORY!!!')
        self.state.save()

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
        common.release_gamestate()
        self.request('app_base')
        if self.isandroid:
            plyer.gravity.disable()
        self.systems.stats.end_session()
        self.systems.stats.close()
        self.state.save()
        self.mps.ctrl.stop()
        super().on_quit()

    def enter_app_base(self):
        """Stub to enable this to become a state."""

    def exit_app_base(self):
        """Stub to enable this to become a state."""
