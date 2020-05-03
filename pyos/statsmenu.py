"""
Provides the stats menu.
"""

from dataclasses import dataclass
from typing import Tuple

from foolysh.scene.node import Origin
from foolysh.ui import button, frame, label

import app
import common

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
class StatsLabel:
    """Labels of Statistics."""
    # pylint: disable=too-many-instance-attributes

    deals_played: label.Label
    solved_ratio: label.Label
    avg_attempts: label.Label
    one_highscore: label.Label
    one_fastest: label.Label
    one_least_moves: label.Label
    three_highscore: label.Label
    three_fastest: label.Label
    three_least_moves: label.Label

    text: Tuple[str] = ('Deals played', 'Solved ratio', 'Avg attempts/deal',
                        'Draw one highscore', 'Draw one quickest',
                        'Draw one least moves', 'Draw three highscore',
                        'Draw three quickest', 'Draw three least moves')

    def __len__(self):
        return 9

    def __getitem__(self, item: int) -> label.Label:
        return [self.deals_played, self.solved_ratio, self.avg_attempts,
                self.one_highscore, self.one_fastest, self.one_least_moves,
                self.three_highscore, self.three_fastest,
                self.three_least_moves][item]


class Statistics(app.AppBase):
    """
    Statistics menu.
    """
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__root = self.ui.center.attach_node('statistics root')
        self.__frame = frame.Frame('statistics background', size=(0.9, 0.9),
                                   frame_color=common.FRAME_COLOR_STD,
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2)
        self.__frame.reparent_to(self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = label.Label(text='Statistics', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt,
                          text_color=common.TITLE_TXT_COLOR, alpha=0)
        tit.reparent_to(self.__frame)
        tit.origin = Origin.CENTER
        self.__labels: StatsLabel = None
        self.__setup()
        self.__root.hide()

    def enter_statistics(self):
        """Enter state -> Setup."""
        self.__root.show()
        self.__update_labels()

    def exit_statistics(self):
        """Exit state -> Setup."""
        self.__root.hide()

    def __update_labels(self):
        vals = [f'{self.stats.deals_played}',
                f'{self.stats.solved_ratio * 100:.3f}%',
                f'{self.stats.avg_attempts + 0.05:.1f}']
        for i in (1, 3):
            val = self.stats.highscore(i)
            if val:
                vals.append(f'{val}')
            else:
                vals.append('     N/A')
            val = self.stats.fastest(i)
            if val == float('inf'):
                vals.append('     N/A')
            else:
                vals.append(f'{int(val / 60)}:{val % 60:06.3f}')
            val = self.stats.least_moves(i)
            if val == 2**32:
                val = '     N/A'
            vals.append(f'{val}')

        maxlen = max(
            [len(i) + len(j) for i, j in zip(self.__labels.text, vals)])
        for txt, lbl, val in zip(self.__labels.text, self.__labels, vals):
            offset = maxlen - len(txt) - len(val)
            lbl.text = f'{txt}: {" " * offset}{val}'

    def __setup(self):
        # pylint: disable=too-many-statements
        tot_height = 0.77
        step_y = tot_height / 11
        pos_y = -0.25
        height = step_y / 1.06
        kwargs = {'font': self.config.get('font', 'bold'),
                  'font_size': 0.042, 'text_color': (0, 50, 0, 255),
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
        lbls = []
        for _ in range(9):
            lbl = self.__create_label(size=(0.34, height), pos=(-0.42, pos_y),
                                      **kwargs)
            lbls.append(lbl)
            pos_y += step_y
        self.__labels = StatsLabel(*lbls)
        kwargs = {'font': self.config.get('font', 'bold'),
                  'text_color': (0, 50, 0, 255), 'frame_color': (200, 220, 200),
                  'down_text_color': (255, 255, 255, 255),
                  'border_thickness': 0.005, 'down_border_thickness': 0.008,
                  'border_color': (0, 50, 0),
                  'down_border_color': (255, 255, 255),
                  'corner_radius': 0.05, 'multi_sampling': 2,
                  'align': 'center', 'size': (0.8, 0.1)}
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        kwargs = common.get_menu_sym_btn_kw()
        but = button.Button(name='back button', pos=(pos_x, -0.38),
                            text=common.BACK_SYM, **kwargs)
        but.origin = Origin.CENTER
        but.reparent_to(self.__frame)
        but.onclick(self.request, 'main_menu')

    def __create_label(self, size, pos, alt_font_size=None, **kwargs):
        fnt_size = alt_font_size or kwargs['font_size']
        lbl = label.Label(text='', size=size, margin=0.01, pos=pos, alpha=0,
                          font=kwargs['font'], font_size=fnt_size)
        lbl.reparent_to(self.__frame)
        return lbl
