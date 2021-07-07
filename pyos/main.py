"""
Entry point of the app.
"""

import configparser
import os
import sys

from loguru import logger
import plyer
try:
    import android  # pylint: disable=unused-import
    from jnius import autoclass
except ImportError:
    pass

import common
import daydeal
import menu
from mpctrl import Request
import mpmenu
import mpchallenge
import mpfriends
import mpleaderboard
import game
import statsmenu

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


class PyOS(menu.MainMenu, menu.SettingsMenu, game.Game, statsmenu.Statistics,
           daydeal.DayDeal, mpmenu.MultiplayerMenu, mpchallenge.Challenges,
           mpfriends.Friends, mpleaderboard.Leaderboard,
           mpmenu.MultiplayerSettings):
    """
    All states collected using multiple inheritance.
    """
    # pylint: disable=too-many-ancestors
    def on_quit(self):
        self.systems.shuffler.stop()
        super().on_quit()


def verify_config(cfg: configparser.ConfigParser, cfg_file: str):
    """Check if all default keys are in the stored configuration."""
    for sec in common.DEFAULTCONFIG:
        if sec not in cfg:
            cfg.add_section(sec)
        for k in common.DEFAULTCONFIG[sec]:
            if cfg.get(sec, k, fallback=None) is None:
                cfg.set(sec, k, common.DEFAULTCONFIG[sec][k])
    for k in common.OVERWRITE_PYOS:
        cfg.set('pyos', k, common.DEFAULTCONFIG['pyos'][k])
    if 'mp' not in cfg:
        cfg.add_section('mp')
        for k in common.DEFAULTCONFIG['mp']:
            cfg.set('mp', k, common.DEFAULTCONFIG['mp'][k])
    else:
        for k in common.OVERWRITE_MP:
            cfg.set('mp', k, common.DEFAULTCONFIG['mp'][k])
    for k in common.OVERWRITE_FONT:
        cfg.set('font', k, common.DEFAULTCONFIG['font'][k])
    cfg.write(open(cfg_file, 'w'))


def start_mpservice():
    """Preemptively start the multiplayer service on android."""
    port_file = common.UDS
    if os.path.exists(port_file):
        with open(port_file, 'r') as fhandler:
            try:
                port = int(fhandler.read())
            except ValueError:
                pass
            else:
                try:
                    _ = Request(0, port, None, {})
                except (NameError, FileNotFoundError, ConnectionRefusedError,
                        BrokenPipeError, ConnectionResetError):
                    pass
                else:
                    return
        os.unlink(port_file)
    if 'autoclass' in globals():
        logger.info('Starting Android Service multiplayer')
        service = autoclass('com.tizilogic.pyos.ServiceMultiplayer')
        # pylint: disable=invalid-name
        mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
        # pylint: enable=invalid-name
        service.start(mActivity, '')


def main(cfg_file):
    """Launches the app."""
    cfg_file = os.path.join(plyer.storagepath.get_application_dir(), cfg_file)
    if not os.path.isfile(cfg_file):
        os.makedirs(os.path.split(cfg_file)[0], exist_ok=True)
        cfg = configparser.ConfigParser()
        cfg.read_dict(common.DEFAULTCONFIG)
        cfg.write(open(cfg_file, 'w'))
    cfg = configparser.ConfigParser()
    cfg.read(cfg_file)
    verify_config(cfg, cfg_file)
    logger.remove()
    # logger.add(sys.stderr, level=cfg.get('pyos', 'log_level'))
    logger.add(sys.stderr, level='DEBUG')
    common.release_gamestate()
    logger.info('pyos starting')
    start_mpservice()
    pyos = PyOS(config_file=cfg_file)
    logger.debug('Request state main_menu')
    pyos.request('main_menu')
    logger.debug('Start main loop')
    pyos.run()
    sys.exit(0)


if __name__ == '__main__':
    try:
        import android  # pylint: disable=unused-import,ungrouped-imports
        CFG = 'com.tizilogic.pyos/files/.foolysh/foolysh.ini'
    except ImportError:
        CFG = '.foolysh/foolysh.ini'
    main(CFG)
