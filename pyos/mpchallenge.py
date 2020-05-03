"""
Provides the Multiplayer Challenge State.
"""
# pylint: disable=too-many-lines

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple

from foolysh.scene import node
from foolysh.scene.node import Origin
from foolysh.ui import button, frame, entry, label
from loguru import logger

import app
import buttonlist
import common
from dialogue import Dialogue, DialogueButton
import mpctrl
import util

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


class Challenges(app.AppBase):
    """Challenges view."""
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__root = self.ui.center.attach_node('MP Challenges Root')
        self.__frame = frame.Frame('challenges background', size=(0.9, 0.9),
                                   frame_color=common.CHALLENGES_FRAME_COLOR,
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2)
        self.__frame.reparent_to(self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = label.Label(text='Challenges', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt,
                          text_color=common.TITLE_TXT_COLOR, alpha=0)
        tit.reparent_to(self.__frame)
        tit.origin = Origin.CENTER
        self.__data: List[str] = []
        self.__fltr: int = None
        self.__btnlist: buttonlist.ButtonList = None
        self.__back: button.Button = None
        self.__new: button.Button = None
        self.__setup_menu_buttons()
        self.__root.hide()

    def enter_challenges(self):
        """Enter state -> Setup."""
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        self.__back.pos = pos_x, -0.38
        self.__new.pos = pos_x, 0.38
        self.__filter(self.__fltr)
        self.__btnlist.update_content()
        self.__root.show()

    def exit_challenges(self):
        """Exit state -> Setup."""
        self.__root.hide()

    def __setup_menu_buttons(self):
        self.__btnlist = common.gen_btnlist(self.config.get('font', 'normal'),
                                            self.config.get('font', 'bold'),
                                            self.__data, (self.__listclick,
                                                          self.__filter), 4,
                                            (0.85, 0.625), self.__frame,
                                            ['My Turn', 'Waiting', 'Finished'])
        self.__btnlist.pos = 0, 0
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        kwargs = common.get_menu_sym_btn_kw()
        newb = button.Button(name='new button', pos=(pos_x, 0.38),
                             text=chr(0xf893), **kwargs)
        newb.origin = Origin.CENTER
        newb.reparent_to(self.__frame)
        newb.onclick(self.__new_challenge)
        back = button.Button(name='back button', pos=(pos_x, -0.38),
                             text=common.BACK_SYM, **kwargs)
        back.origin = Origin.CENTER
        back.reparent_to(self.__frame)
        back.onclick(self.request, 'multiplayer_menu')
        self.__back = back
        self.__new = newb

    def __new_challenge(self):
        # TODO: Open New Challenge Dialogue
        pass

    def __filter(self, fltr: int = None) -> None:
        # TODO: Update the content of the data list
        pass

    def __listclick(self, pos: int) -> None:
        print(f'clicked on "{self.__data[pos]}"')
        # TODO: Open Challenge Dialogue
