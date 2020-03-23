"""
Provides the daily deal menu.
"""

import datetime
import struct
from typing import Dict, List

from foolysh.scene.layout import GridLayout
from foolysh.scene.node import Origin
from foolysh.ui import button, frame, label, UIState

import app
from common import START_DATE
from dialogue import Dialogue, DialogueButton

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


def unpack_seeds(fpath: str) -> Dict[int, List[int]]:
    """Unpack the seeds file."""
    ones, threes = [], []
    with open(fpath, 'rb') as fptr:
        while True:
            k = fptr.read(8)
            if not k:
                break
            one, three = struct.unpack('<ii', k)
            ones.append(one)
            threes.append(three)
    return {1: ones, 3: threes}


class DayDeal(app.AppBase):
    """Daily deal menu."""
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__root = self.ui.center.attach_node('daydeal root')
        self.__frame = frame.Frame('daydeal background', size=(0.9, 0.9),
                                   frame_color=(40, 120, 20),
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2)
        self.__frame.reparent_to(self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = self.__frame.attach_text_node(text='Daily Deal - Draw one',
                                            font_size=0.06, font=fnt,
                                            text_color=(255, 255, 255, 255))
        tit.pos = -0.38, -0.42
        tit = self.__frame.attach_text_node(text='Daily Deal - Draw three',
                                            font_size=0.06, font=fnt,
                                            text_color=(255, 255, 255, 255))
        tit.pos = -0.41, -0.05

        self.__grid_o = GridLayout(self.__frame, (0, 0, 0.8, 0.25), (2, ),
                                   (5,), (0.01, 0.01))
        self.__grid_o._root.pos = -0.4, -0.35
        self.__grid_t = GridLayout(self.__frame, (0, 0, 0.8, 0.25), (2, ),
                                   (5,), (0.01, 0.01))
        self.__grid_t._root.pos = -0.4, 0.0
        self.__buttons: Dict[int, List[button.Button]] = {1: [], 3: []}
        self.__dailyseeds = unpack_seeds(self.config.get('pyos', 'dailyseeds'))
        self.__dlg: Dialogue = None
        self.__setup()
        self.__root.hide()

    def enter_day_deal(self):
        """Enter state -> Setup."""
        self.__root.show()
        self.__update()

    def exit_day_deal(self):
        """Exit state -> Setup."""
        self.__root.hide()

    def __click(self, draw: int, seed: int, score: bool = False,
                day: str = '') -> None:
        if score:
            txt = f'{day}\n\n'
            dur, moves, pts, bonus = self.stats.result(seed, draw, True, True)
            dur = f'{int(dur / 60)}:{dur % 60:5.2f}'
            moves = f'{moves}'
            pts = f'{pts}'
            bonus = f'{bonus}'
            mlen = max([len(dur), len(moves), len(pts), len(bonus)])
            txt += f'Time: {" " * (mlen - len(dur))}{dur}\n'
            txt += f'Moves: {" " * (mlen - len(moves))}{moves}\n'
            txt += f'Points:  {" " * (mlen - len(pts))}{pts}\n'
            txt += f'Bonus:  {" " * (mlen - len(bonus))}{bonus}\n'
            self.__gen_dlg(txt)
        else:
            self.daydeal = draw, seed
            self.shuffler.request_deal(draw, seed)
            self.request('game')

    def __hide_dlg(self):
        self.__dlg.hide()
        self.__frame.show()

    def __gen_dlg(self, txt: str):
        if self.__dlg is None:
            fnt = self.config.get('font', 'bold')
            buttons = [DialogueButton(text='Close',
                                      fmtkwargs={'size': (0.35, 0.1),
                                                 'font': fnt,
                                                 'text_color': (0, 50, 0, 255),
                                                 'down_text_color': (255, 255,
                                                                     255, 255),
                                                 'border_thickness': 0.005,
                                                 'down_border_thickness': 0.008,
                                                 'border_color': (0, 50, 0),
                                                 'down_border_color': (255, 255,
                                                                       255),
                                                 'corner_radius': 0.05,
                                                 'multi_sampling': 2,
                                                 'align': 'center'},
                                      callback=self.__hide_dlg)]
            dlg = Dialogue(text=txt, buttons=buttons, margin=0.01,
                           size=(0.7, 0.7), font=fnt, align='center',
                           frame_color=(40, 120, 20), border_thickness=0.01,
                           corner_radius=0.05, multi_sampling=2)
            dlg.pos = -0.35, -0.35
            dlg.reparent_to(self.ui.center)
            dlg.depth = 1000
            self.__dlg = dlg
        else:
            self.__dlg.text = txt
            self.__dlg.show()
        self.__frame.hide()

    def __update(self):
        today = datetime.datetime.utcnow()
        start_i = today - START_DATE - datetime.timedelta(days=9)
        for i in range(10):
            day = today + datetime.timedelta(days=i - 9)
            sday = f'{day.month}/{day.day}'
            for k in (1, 3):
                seed = self.__dailyseeds[k][start_i.days + i]
                btn = self.__buttons[k][i]
                if self.stats.issolved(seed, k, True, True):
                    btn.onclick(self.__click, k, seed, True, sday)
                    btn.labels[UIState.NORMAL].frame_color = (40, 150, 20)
                else:
                    btn.onclick(self.__click, k, seed)
                    btn.labels[UIState.NORMAL].frame_color = (150, ) * 3
                for lbl in btn.labels:
                    lbl.text = sday


    def __setup(self):
        # pylint: disable=too-many-statements
        kwargs = {'font': self.config.get('font', 'bold'),
                  'font_size': 0.045, 'text_color': (255, 255, 255, 225),
                  'down_text_color': (255, 255, 255, 255),
                  'border_thickness': 0.005,
                  'border_color': (0, 50, 0),
                  'corner_radius': 0.01, 'multi_sampling': 2,
                  'align': 'center', 'margin': 0.01}
        for row in range(2):
            for col in range(5):
                for i, grid in ((1, self.__grid_o), (3, self.__grid_t)):
                    parent = grid[row, col]
                    lbl = self.__create_button(parent.size, (0, 0), **kwargs)
                    lbl.reparent_to(parent)
                    self.__buttons[i].append(lbl)
        kwargs = {'font': self.config.get('font', 'bold'),
                  'text_color': (0, 50, 0, 255), 'frame_color': (200, 220, 200),
                  'down_text_color': (255, 255, 255, 255),
                  'border_thickness': 0.005, 'down_border_thickness': 0.008,
                  'border_color': (0, 50, 0),
                  'down_border_color': (255, 255, 255),
                  'corner_radius': 0.05, 'multi_sampling': 2,
                  'align': 'center', 'size': (0.8, 0.1)}
        back = button.Button(name='back button', pos=(0, 0.375),
                             text='Back',
                             **kwargs)
        back.origin = Origin.CENTER
        back.reparent_to(self.__frame)
        back.onclick(self.request, 'main_menu')

    def __create_button(self, size, pos, alt_font_size=None, **kwargs):
        kwa = {}
        kwa.update(kwargs)
        kwa['font_size'] = alt_font_size or kwargs['font_size']
        btn = button.Button(text='', size=size, pos=pos, **kwa)
        btn.reparent_to(self.__frame)
        return btn
