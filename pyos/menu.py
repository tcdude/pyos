"""
Provides the different menus in the app.
"""

from dataclasses import dataclass
import os
from typing import Tuple

from foolysh.scene.node import Origin
from foolysh.ui import button, frame, label
from loguru import logger

import app
import common
import mpctrl

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
class MenuButtons:
    """Buttons of the main menu."""
    play: button.Button
    daydeal: button.Button
    stats: button.Button
    multiplayer: button.Button
    settings: button.Button
    quit: button.Button


class MainMenu(app.AppBase):
    """
    Main menu of the app. Shown on start and when exiting from other states.
    """
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__root = self.ui.center.attach_node('Menu Root')
        self.__frame = frame.Frame('main menu background', size=(0.9, 0.9),
                                   frame_color=common.FRAME_COLOR_STD,
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2, parent=self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = self.__frame.attach_text_node(text='Adfree Simple Solitaire',
                                            font_size=0.06, font=fnt,
                                            text_color=common.TITLE_TXT_COLOR)
        tit.pos = -0.41, -0.3
        verfile = os.path.join(self.config.get('base', 'asset_dir'),
                               'other/VERSION')
        with open(verfile, 'r') as fhandler:
            version = fhandler.read().strip()
        self.__ver = self.__frame \
            .attach_text_node(text=f'v{version}', font_size=0.04, font=fnt,
                              text_color=common.TITLE_TXT_COLOR)
        self.__ver.pos = -0.1, 0.4
        self.__buttons: MenuButtons = None
        self.__pending_sync: int = 0
        self.__setup_menu_buttons()
        self.__root.hide()

    def enter_main_menu(self):
        """Enter state -> Setup."""
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        cbk = self.__update_btns, (), {}
        self.mps.notification_callback['main_menu'] = cbk
        self.__buttons.settings.pos = pos_x, 0.38
        self.__buttons.quit.pos = pos_x, -0.38
        self.__root.show()
        req = self.mps.ctrl.nop()
        self.mps.ctrl.register_callback(req, self.__enable_quit)
        if req < 0:
            logger.warning(f'Unable to start request to multiplayer service')
            self.__buttons.quit.enabled = True
        else:
            self.__buttons.quit.enabled = False
        self.__buttons.multiplayer.enabled = False
        if 'firstopen' not in self.fsm_global_data:
            self.fsm_global_data['firstopen'] = None
        else:
            self.login('Checking connection...')

    def exit_main_menu(self):
        """Exit state -> Setup."""
        self.mps.notification_callback.pop('main_menu')
        self.__root.hide()

    def __enable_quit(self, rescode: int) -> None:
        if self.__ver.size[0] > 0:
            self.__ver.x = -self.__ver.size[0] / 2
        self.__buttons.quit.enabled = True
        self.__buttons.multiplayer.enabled = True
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
        if self.mps.login == 0:
            user = self.config.get('mp', 'user')
            self.global_nodes.set_mpstatus(f'Logged in as {user}')
            req = self.mps.ctrl.sync_challenges()
            self.mps.ctrl.register_callback(req, self.__update_notifications)
            self.__pending_sync = 1
            self.global_nodes.show_status('Updating notifications...')

    def __update_notifications(self, rescode: int) -> None:
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
        self.__pending_sync -= 1
        if self.__pending_sync:
            return
        self.global_nodes.hide_status()
        self.__update_btns(self.mps.dbh.challenge_actions,
                           self.mps.dbh.friend_actions)
        reqs = common.submit_dd_results(self.systems.stats, self.mps.dbh,
                                        self.mps.ctrl)
        for req, day, draw in reqs:
            logger.debug(f'Sending result for D{draw} #{day}')
            self.global_nodes.show_status('Submitting Daydeal Scores...')
            self.__pending_sync += 1
            self.mps.ctrl.register_callback(req, self.__submit_ddcb, day, draw)

    def __update_btns(self, cha: int, fra: int) -> None:
        act = cha + fra
        txt = chr(0xf6e6) + ' Multiplayer '
        txt += common.bubble_number(act) if act else chr(0xf6e6)
        self.__buttons.multiplayer.change_text(txt)
        col = common.NTFY_MENU_TXT_COLOR if act else common.STD_MENU_TXT_COLOR
        self.__buttons.multiplayer.labels[0].text_color = col

    def __submit_ddcb(self, rescode: int, day: int, draw: int) -> None:
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
        elif day is not None and rescode == 0:
            logger.debug(f'Result D{draw} #{day} submitted')
            self.mps.dbh.update_dd_score(draw, day, sent=True)
        self.__pending_sync -= 1
        if self.__pending_sync:
            return
        self.global_nodes.hide_status()

    def __setup_menu_buttons(self):
        kwargs = common.get_menu_txt_btn_kw(size=(0.8, 0.1))
        offset = 0.125
        pos_y = -0.14
        txt = chr(0xf90b) + ' ' * 5 + 'Play' + ' ' * 5 + chr(0xf90b)
        play = button.Button(name='play button', pos=(0, pos_y), text=txt,
                             parent=self.__frame, **kwargs)
        play.origin = Origin.CENTER
        play.onclick(self.request, 'game')
        pos_y += offset
        txt = chr(0xf274) + '  Daily Deal  ' + chr(0xf274)
        daydeal = button.Button(name='daydeal button', pos=(0, pos_y), text=txt,
                                parent=self.__frame, **kwargs)
        daydeal.origin = Origin.CENTER
        daydeal.onclick(self.request, 'day_deal')
        pos_y += offset
        txt = '' + chr(0xf201) + '  Statistics  ' + chr(0xf201)
        stats = button.Button(name='stats button', pos=(0, pos_y), text=txt,
                              parent=self.__frame, **kwargs)
        stats.origin = Origin.CENTER
        stats.onclick(self.request, 'statistics')
        pos_y += offset
        txt = chr(0xf6e6) + ' Multiplayer ' + chr(0xf6e6)
        multiplayer = button.Button(name='Multiplayer', pos=(0, pos_y),
                                    text=txt, parent=self.__frame, **kwargs)
        multiplayer.origin = Origin.CENTER
        multiplayer.onclick(self.request, 'multiplayer_menu')
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        kwargs.update(common.MENU_SYM_BTN_KW)
        settings = button.Button(name='settings button', pos=(pos_x, 0.38),
                                 text=chr(0xf013), parent=self.__frame,
                                 **kwargs)
        settings.origin = Origin.CENTER
        settings.onclick(self.request, 'settings_menu')
        quitb = button.Button(name='quit button', pos=(pos_x, -0.38),
                              text=chr(0xf705), parent=self.__frame, **kwargs)
        quitb.origin = Origin.CENTER
        quitb.onclick(self.quit, blocking=False)
        self.__buttons = MenuButtons(play, daydeal, stats, multiplayer,
                                     settings, quitb)


@dataclass
class SettingsButtons:
    """Buttons/Controls of settings."""
    # pylint: disable=too-many-instance-attributes

    readability: button.Button
    draw_one: button.Button
    draw_three: button.Button
    tap_move: button.Button
    waste_to_foundation: button.Button
    waste_to_tableau: button.Button
    auto_solve: button.Button
    auto_flip: button.Button
    left_handed: button.Button
    orientation: button.Button
    back: button.Button


class SettingsMenu(app.AppBase):
    """
    Settings menu.
    """
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__root = self.ui.center.attach_node('SubMenu Root')
        self.__frame = frame.Frame('sub menu background', size=(0.9, 0.9),
                                   frame_color=common.SETTINGS_FRAME_COLOR,
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2, parent=self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = label.Label(text='App Settings', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt,
                          text_color=common.TITLE_TXT_COLOR, alpha=0,
                          parent=self.__frame)
        tit.origin = Origin.CENTER
        self.__buttons: SettingsButtons = None
        self.__setup()
        self.__root.hide()

    def enter_settings_menu(self):
        """Enter state -> Setup."""
        self.__update_button_pos()
        self.__root.show()

    def exit_settings_menu(self):
        """Exit state -> Setup."""
        self.__root.hide()

    def __update_button_pos(self):
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        self.__buttons.back.pos = pos_x, -0.38

    def __toggle(self, key: str, but: button.Button,
                 txts: Tuple[str, str] = ('On', 'Off')) -> None:
        if self.config.getboolean('pyos', key):
            self.config.set('pyos', key, 'False')
            txt = txts[1]
        else:
            self.config.set('pyos', key, 'True')
            txt = txts[0]
        self.update_cards()
        but.change_text(txt)

    def __click(self, task: str) -> None:
        # pylint: disable=too-many-branches
        if task == 'readability':
            self.__toggle(task, self.__buttons.readability)
            self.state.layout_refresh = True
        elif task == 'draw_one':
            self.config.set('pyos', 'draw_one', 'True')
            self.__buttons.draw_one.enabled = False
            self.__buttons.draw_three.enabled = True
            self.state.layout_refresh = True
            self.state.need_new_game = True
        elif task == 'draw_three':
            self.config.set('pyos', 'draw_one', 'False')
            self.__buttons.draw_one.enabled = True
            self.__buttons.draw_three.enabled = False
            self.state.layout_refresh = True
            self.state.need_new_game = True
        elif task == 'tap_move':
            self.__toggle(task, self.__buttons.tap_move)
        elif task == 'foundation':
            self.config.set('pyos', 'waste_to_foundation', 'True')
            self.__buttons.waste_to_foundation.enabled = False
            self.__buttons.waste_to_tableau.enabled = True
        elif task == 'tableau':
            self.config.set('pyos', 'waste_to_foundation', 'False')
            self.__buttons.waste_to_foundation.enabled = True
            self.__buttons.waste_to_tableau.enabled = False
        elif task == 'auto_solve':
            self.__toggle(task, self.__buttons.auto_solve)
        elif task == 'auto_flip':
            self.__toggle(task, self.__buttons.auto_flip)
        elif task == 'left_handed':
            self.__toggle(task, self.__buttons.left_handed, ('Left', 'Right'))
            self.__update_button_pos()
            self.state.layout_refresh = True
        elif task == 'orientation':
            orient = self.config.get('pyos', 'orientation', fallback='auto')
            if orient == 'auto':
                txt = 'Portrait'
            elif orient == 'portrait':
                txt = 'Landscape'
            else:
                txt = 'Auto'
            self.config.set('pyos', 'orientation', txt.lower())
            for i in self.__buttons.orientation.labels:
                i.text = txt
        elif task == 'back':
            self.request('main_menu')
        else:
            raise ValueError(f'Got unexpected button "{task}".')
        self.config.save()

    def __setup(self):
        # pylint: disable=too-many-statements
        tot_height = 0.79
        step_y = tot_height / 8.5
        pos_y = -0.32
        height = step_y / 1.1
        kwargs = common \
            .get_settings_btn_kw(font_size=0.0355,
                                 border_thickness=height * 0.043,
                                 down_border_thickness=height * 0.06,
                                 disabled_border_thickness=height * 0.043,
                                 corner_radius=height / 2)
        buttons = []
        self.__create_label(text='Simple Deck:', size=(0.34, height),
                            pos=(-0.42, pos_y), **kwargs)
        txt = 'On' if self.config.getboolean('pyos', 'readability') else 'Off'
        but = self.__create_button(text=txt, size=(0.15, height),
                                   pos=(-0.05, pos_y), **kwargs)
        but.onclick(self.__click, 'readability')
        buttons.append(but)
        pos_y += step_y

        self.__create_label(text='Draw Count:', size=(0.34, height),
                            pos=(-0.42, pos_y), **kwargs)
        but = self.__create_button(text='One', size=(0.15, height),
                                   pos=(-0.05, pos_y), **kwargs)
        but.onclick(self.__click, 'draw_one')
        if self.config.getboolean('pyos', 'draw_one'):
            but.enabled = False
        buttons.append(but)
        but = self.__create_button(text='Three', size=(0.2, height),
                                   pos=(0.12, pos_y), **kwargs)
        but.onclick(self.__click, 'draw_three')
        if not self.config.getboolean('pyos', 'draw_one'):
            but.enabled = False
        buttons.append(but)
        pos_y += step_y

        self.__create_label(text='Tap to move:', size=(0.34, height),
                            pos=(-0.42, pos_y), **kwargs)
        txt = 'On' if self.config.getboolean('pyos', 'tap_move') else 'Off'
        but = self.__create_button(text=txt, size=(0.15, height),
                                   pos=(-0.05, pos_y), **kwargs)
        but.onclick(self.__click, 'tap_move')
        buttons.append(but)
        pos_y += step_y

        self.__create_label(text='Preferred Move:',
                            size=(0.34, height), pos=(-0.42, pos_y),
                            alt_font_size=kwargs['font_size'] * 0.94, **kwargs)
        but = self.__create_button(text='Foundation', size=(0.225, height),
                                   pos=(-0.05, pos_y),
                                   alt_font_size=kwargs['font_size'] * 0.8,
                                   **kwargs)
        but.onclick(self.__click, 'foundation')
        if self.config.getboolean('pyos', 'waste_to_foundation'):
            but.enabled = False
        buttons.append(but)
        but = self.__create_button(text='Tableau', size=(0.225, height),
                                   pos=(0.195, pos_y),
                                   alt_font_size=kwargs['font_size'] * 0.8,
                                   **kwargs)
        but.onclick(self.__click, 'tableau')
        if not self.config.getboolean('pyos', 'waste_to_foundation'):
            but.enabled = False
        buttons.append(but)
        pos_y += step_y

        self.__create_label(text='Auto Solve:', size=(0.34, height),
                            pos=(-0.42, pos_y), **kwargs)
        txt = 'On' if self.config.getboolean('pyos', 'auto_solve') else 'Off'
        but = self.__create_button(text=txt, size=(0.15, height),
                                   pos=(-0.05, pos_y), **kwargs)
        but.onclick(self.__click, 'auto_solve')
        buttons.append(but)
        pos_y += step_y

        self.__create_label(text='Auto Flip:', size=(0.34, height),
                            pos=(-0.42, pos_y), **kwargs)
        txt = 'On' if self.config.getboolean('pyos', 'auto_flip') else 'Off'
        but = self.__create_button(text=txt, size=(0.15, height),
                                   pos=(-0.05, pos_y), **kwargs)
        but.onclick(self.__click, 'auto_flip')
        buttons.append(but)
        pos_y += step_y

        self.__create_label(text='Handedness:', size=(0.34, height),
                            pos=(-0.42, pos_y), **kwargs)
        txt = 'Right'
        if self.config.getboolean('pyos', 'left_handed'):
            txt = 'Left'
        but = self.__create_button(text=txt, size=(0.2, height),
                                   pos=(-0.05, pos_y), **kwargs)
        but.onclick(self.__click, 'left_handed')
        buttons.append(but)
        pos_y += step_y

        kwargs['align'] = 'left'
        self.__create_label(text='Orientation:', size=(0.34, height),
                            pos=(-0.42, pos_y), **kwargs)
        txt = self.config.get('pyos', 'orientation', fallback='auto')
        txt = txt.capitalize()
        but = self.__create_button(text=txt, size=(0.3, height),
                                   pos=(-0.05, pos_y), **kwargs)
        but.onclick(self.__click, 'orientation')
        buttons.append(but)
        pos_y += step_y

        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        kwargs = common.get_menu_sym_btn_kw()
        but = button.Button(name='back button', pos=(pos_x, -0.38),
                            text=common.BACK_SYM, parent=self.__frame, **kwargs)
        but.origin = Origin.CENTER
        but.onclick(self.request, 'main_menu')
        buttons.append(but)
        self.__buttons = SettingsButtons(*buttons)

    def __create_button(self, text, size, pos, alt_font_size=None, **kwargs):
        kwa = {}
        kwa.update(kwargs)
        if alt_font_size:
            kwa['font_size'] = alt_font_size
        but = button.Button(name=f'{text} but', text=text, size=size, pos=pos,
                            parent=self.__frame, **kwa)
        return but

    def __create_label(self, text, size, pos, alt_font_size=None, **kwargs):
        fnt_size = alt_font_size or kwargs['font_size']
        _ = label.Label(text=text, size=size, margin=0.01, pos=pos, alpha=0,
                        font=kwargs['font'], font_size=fnt_size,
                        parent=self.__frame)
