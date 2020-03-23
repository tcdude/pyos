"""
Provides the different menus in the app.
"""

from dataclasses import dataclass
from typing import Tuple

from foolysh.scene.node import Origin
from foolysh.ui import button, frame, label

import app

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


@dataclass
class MenuButtons:
    """Buttons of the main menu."""
    play: button.Button
    daydeal: button.Button
    stats: button.Button
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
                                   frame_color=(40, 120, 20),
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2)
        self.__frame.reparent_to(self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = self.__frame.attach_text_node(text='Adfree Simple Solitaire',
                                            font_size=0.06, font=fnt,
                                            text_color=(255, 255, 255, 255))
        tit.pos = -0.4, -0.4
        self.__buttons: MenuButtons = None
        self.__setup_menu_buttons()
        self.__root.hide()

    def enter_main_menu(self):
        """Enter state -> Setup."""
        self.__root.show()

    def exit_main_menu(self):
        """Exit state -> Setup."""
        self.__root.hide()

    def __setup_menu_buttons(self):
        kwargs = {'font': self.config.get('font', 'bold'),
                  'text_color': (0, 50, 0, 255), 'frame_color': (200, 220, 200),
                  'down_text_color': (255, 255, 255, 255),
                  'border_thickness': 0.005, 'down_border_thickness': 0.008,
                  'border_color': (0, 50, 0),
                  'down_border_color': (255, 255, 255),
                  'corner_radius': 0.05, 'multi_sampling': 2,
                  'align': 'center', 'size': (0.8, 0.1)}
        offset = 0.125
        pos_y = -0.2
        play = button.Button(name='play button', pos=(0, pos_y),
                             text=chr(0xf90b) + ' Play    ',
                             **kwargs)
        play.origin = Origin.CENTER
        play.reparent_to(self.__frame)
        play.onclick(self.request, 'game')
        pos_y += offset
        daydeal = button.Button(name='daydeal button', pos=(0, pos_y),
                                text=chr(0xf274) + ' Daily Deal', **kwargs)
        daydeal.origin = Origin.CENTER
        daydeal.reparent_to(self.__frame)
        daydeal.onclick(self.request, 'day_deal')
        pos_y += offset
        stats = button.Button(name='stats button', pos=(0, pos_y),
                              text='' + chr(0xf201) + ' Statistics', **kwargs)
        stats.origin = Origin.CENTER
        stats.reparent_to(self.__frame)
        stats.onclick(self.request, 'statistics')
        pos_y += offset
        settings = button.Button(name='settings button', pos=(0, pos_y),
                                 text=chr(0xf425) + ' Settings', **kwargs)
        settings.origin = Origin.CENTER
        settings.reparent_to(self.__frame)
        settings.onclick(self.request, 'settings_menu')
        pos_y += offset
        quitb = button.Button(name='quit button', pos=(0, pos_y),
                              text=chr(0xf705)+ ' Quit    ', **kwargs)
        quitb.origin = Origin.CENTER
        quitb.reparent_to(self.__frame)
        quitb.onclick(self.quit, blocking=False)
        self.__buttons = MenuButtons(play, daydeal, stats, settings, quitb)


@dataclass
class SettingsButtons:
    """Buttons/Controls of settings."""
    # pylint: disable=too-many-instance-attributes

    winner_deal: button.Button
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
                                   frame_color=(160, 90, 40),
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2)
        self.__frame.reparent_to(self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = self.__frame.attach_text_node(text='Settings',
                                            font_size=0.06, font=fnt,
                                            text_color=(255, 255, 255, 255))
        tit.pos = -0.15, -0.42
        self.__buttons: SettingsButtons = None
        self.__setup()
        self.__root.hide()

    def enter_settings_menu(self):
        """Enter state -> Setup."""
        self.__root.show()

    def exit_settings_menu(self):
        """Exit state -> Setup."""
        self.__root.hide()

    def __toggle(self, key: str, but: button.Button,
                 txts: Tuple[str, str] = ('On', 'Off')) -> None:
        if self.config.getboolean('pyos', key):
            self.config.set('pyos', key, 'False')
            txt = txts[1]
        else:
            self.config.set('pyos', key, 'True')
            txt = txts[0]
        for i in but.labels:
            i.text = txt

    def __click(self, task: str) -> None:
        if task == 'winner_deal':
            self.__toggle(task, self.__buttons.winner_deal)
        elif task == 'draw_one':
            self.config.set('pyos', 'draw_one', 'True')
            self.__buttons.draw_one.enabled = False
            self.__buttons.draw_three.enabled = True
            self.layout_refresh = True
            self.need_new_game = True
        elif task == 'draw_three':
            self.config.set('pyos', 'draw_one', 'False')
            self.__buttons.draw_one.enabled = True
            self.__buttons.draw_three.enabled = False
            self.layout_refresh = True
            self.need_new_game = True
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
            self.layout_refresh = True
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
        tot_height = 0.77
        step_y = tot_height / 9
        pos_y = -0.35
        height = step_y / 1.06
        kwargs = {'font': self.config.get('font', 'bold'),
                  'font_size': 0.0355, 'text_color': (0, 50, 0, 255),
                  'down_text_color': (255, 255, 255, 255),
                  'border_thickness': height * 0.043,
                  'down_border_thickness': height * 0.06,
                  'disabled_border_thickness': height * 0.043,
                  'border_color': (0, 50, 0),
                  'down_border_color': (255, 255, 255),
                  'disabled_text_color': (255, 255, 255, 255),
                  'disabled_frame_color': (160, 160, 160),
                  'disabled_border_color': (255, 255, 255),
                  'corner_radius': height / 2, 'multi_sampling': 2,
                  'align': 'center', 'margin': 0.01}

        buttons = []
        self.__create_label(text='Winner Deal:', size=(0.34, height),
                            pos=(-0.42, pos_y), **kwargs)
        txt = 'On' if self.config.getboolean('pyos', 'winner_deal') else 'Off'
        but = self.__create_button(text=txt, size=(0.15, height),
                                   pos=(-0.05, pos_y), **kwargs)
        but.onclick(self.__click, 'winner_deal')
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

        kwargs['align'] = 'center'
        but = self.__create_button(text='Back', size=(0.84, height),
                                   pos=(-0.42, 0.43 - height), **kwargs)
        but.onclick(self.__click, 'back')
        buttons.append(but)
        self.__buttons = SettingsButtons(*buttons)

    def __create_button(self, text, size, pos, alt_font_size=None, **kwargs):
        kwa = {}
        kwa.update(kwargs)
        if alt_font_size:
            kwa['font_size'] = alt_font_size
        but = button.Button(name=f'{text} but', text=text, size=size, pos=pos,
                            **kwa)
        but.reparent_to(self.__frame)
        return but

    def __create_label(self, text, size, pos, alt_font_size=None, **kwargs):
        fnt_size = alt_font_size or kwargs['font_size']
        lbl = label.Label(text=text, size=size, margin=0.01, pos=pos, alpha=0,
                          font=kwargs['font'], font_size=fnt_size)
        lbl.reparent_to(self.__frame)
