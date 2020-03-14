"""
Entry point of the app.
"""

import configparser
import os
import sys

from loguru import logger

import common
import menu
import game

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


class PyOS(menu.MainMenu, menu.SettingsMenu, game.Game):
    """
    All states collected using multiple inheritance.
    """
    def on_quit(self):
        shf = self.shuffler
        if shf is not None:
            shf.stop()
        super().on_quit()


def main():
    """Launches the app."""
    logger.info('pyos starting')
    cfg_file = '.foolysh/foolysh.ini'
    if not os.path.isfile(cfg_file):
        os.makedirs(os.path.split(cfg_file)[0])
        cfg = configparser.ConfigParser()
        cfg.read_dict(common.DEFAULTCONFIG)
        cfg.write(open(cfg_file, 'w'))
    pyos = PyOS(config_file=cfg_file)
    logger.debug('Request state main_menu')
    pyos.request('main_menu')
    logger.debug('Start main loop')
    pyos.run()
    sys.exit(0)


if __name__ == '__main__':
    main()
