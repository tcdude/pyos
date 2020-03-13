"""
Provides the base class for all states and all attributes/methods that are
shared with all the states.
"""

from loguru import logger
import sdl2

from foolysh import app

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
__version__ = '0.2'


class AppBase(app.App):
    """
    Serves as base for all states registered through multiple inheritance. All
    attributes, properties and methods that are shared across the app are
    defined in this class.
    """
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__setup_events_tasks()
        self.layout_refresh = False
        self.need_new_game = False

    def __setup_events_tasks(self):
        """Setup Events and Tasks."""
        logger.debug('Setting up global events and tasks')
        self.event_handler.listen('quit', sdl2.SDL_QUIT, self.quit,
                                  blocking=False)
        self.event_handler.listen('android_back', sdl2.SDL_KEYUP, self.__back)
        if self.isandroid:
            self.event_handler.listen('APP_TERMINATING',
                                      sdl2.SDL_APP_TERMINATING, self.quit,
                                      blocking=False)
            self.event_handler.listen('APP_WILLENTERBACKGROUND',
                                      sdl2.SDL_APP_WILLENTERBACKGROUND,
                                      self.__event_will_enter_bg)
            self.event_handler.listen('APP_DIDENTERBACKGROUND',
                                      sdl2.SDL_APP_DIDENTERBACKGROUND,
                                      self.__event_pause)
            self.event_handler.listen('APP_LOWMEMORY', sdl2.SDL_APP_LOWMEMORY,
                                      self.__event_low_memory)

    def __back(self, event):
        """Handles Android Back, Escape and Backspace Events"""
        if event.key.keysym.sym in (sdl2.SDLK_AC_BACK, 27, sdl2.SDLK_BACKSPACE):
            self.quit(blocking=False)

    def __event_pause(self, event=None):
        """Called when the app enters background."""
        # pylint: disable=unused-argument
        logger.info('Paused game')
        self.request('app_base')

    def __event_will_enter_bg(self, event=None):
        """Called when the os announces that the app will enter background."""
        # pylint: disable=unused-argument
        logger.warning('Unhandled event APP_WILLENTERBACKGROUND!!!')
        self.request('app_base')

    def __event_low_memory(self, event=None):
        """Called when the os announces low memory."""
        # pylint: disable=unused-argument
        logger.warning('Unhandled event APP_LOWMEMORY!!!')

    def on_quit(self):
        """Overridden on_quit event to make sure the state is saved."""
        logger.info('Saving state and quitting pyos')
        self.request('app_base')

    def enter_app_base(self):
        """Just to trigger the exit_ event of the current active state."""

    def exit_app_base(self):
        """Stub to enable this to become a state."""
