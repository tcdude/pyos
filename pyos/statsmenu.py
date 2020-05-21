"""
Provides the stats menu.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from foolysh.scene.node import Node, Origin
from foolysh.ui import button, frame, label

import app
import buttonlist
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
class StatsData:
    """Holds data fields for the listview."""
    data: List[str] = field(default_factory=list)
    fltr: int = None
    idmap: Dict[int, int] = field(default_factory=dict)
    text: Tuple[str] = ('Deals played', 'Solved ratio', 'Avg attempts/deal',
                        'Draw one highscore', 'Draw one quickest',
                        'Draw one least moves', 'Draw three highscore',
                        'Draw three quickest', 'Draw three least moves')


@dataclass
class StatsNodes:
    """Holds nodes for the statistics view."""
    root: Node = None
    frame: Node = None
    back: button.Button = None
    btnlist: buttonlist.ButtonList = None


class Statistics(app.AppBase):
    """
    Statistics menu.
    """
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__nodes = StatsNodes()
        self.__nodes.root = self.ui.center.attach_node('statistics root')
        self.__nodes.frame = frame \
            .Frame('statistics background', size=(0.9, 0.9),
                   frame_color=common.FRAME_COLOR_STD, border_thickness=0.01,
                   corner_radius=0.05, multi_sampling=2)
        self.__nodes.frame.reparent_to(self.__nodes.root)
        self.__nodes.frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = label.Label(text='Statistics', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt,
                          text_color=common.TITLE_TXT_COLOR, alpha=0)
        tit.reparent_to(self.__nodes.frame)
        tit.origin = Origin.CENTER
        self.__data: StatsData = StatsData()
        self.__setup()
        self.__nodes.root.hide()

    def enter_statistics(self):
        """Enter state -> Setup."""
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        self.__nodes.back.pos = pos_x, -0.38
        self.__nodes.root.show()
        self.__filter(self.__data.fltr)

    def exit_statistics(self):
        """Exit state -> Setup."""
        self.__nodes.root.hide()

    def __setup(self) -> None:
        fnt = self.config.get('font', 'bold')
        self.__nodes.btnlist = common \
            .gen_btnlist(self.config.get('font', 'normal'), fnt,
                         self.__data.data, (self.__listclick, self.__filter), 6,
                         (0.85, 0.7), self.__nodes.frame,
                         ['Offline', 'Online', 'Misc'])
        self.__nodes.btnlist.pos = 0, 0.06
        self.__nodes.btnlist.update_filter(1, enabled=False)
        self.__nodes.btnlist.update_filter(2, enabled=False)
        kwargs = common.get_menu_sym_btn_kw(text_color=common.TITLE_TXT_COLOR)
        self.__nodes.back = button.Button(name='back button',
                                          pos=(0, -0.38),
                                          text=common.BACK_SYM,
                                          **kwargs)
        self.__nodes.back.origin = Origin.CENTER
        self.__nodes.back.reparent_to(self.__nodes.frame)
        self.__nodes.back.onclick(self.__back)

    def __update_data(self) -> None:
        self.__data.data.clear()
        mth = (self.__update_offline, self.__update_online, self.__update_misc)
        mth[self.__data.fltr or 0]()
        self.__nodes.btnlist.update_content()

    def __update_offline(self) -> None:
        vals = [f'{self.systems.stats.deals_played}',
                f'{self.systems.stats.solved_ratio * 100:.3f}%',
                f'{self.systems.stats.avg_attempts + 0.05:.1f}']
        for i in (1, 3):
            val = self.systems.stats.highscore(i)
            if val:
                vals.append(f'{val}')
            else:
                vals.append('     N/A')
            val = self.systems.stats.fastest(i)
            if val == float('inf'):
                vals.append('     N/A')
            else:
                vals.append(f'{int(val / 60)}:{val % 60:06.3f}')
            val = self.systems.stats.least_moves(i)
            if val == 2**32:
                val = '     N/A'
            vals.append(f'{val}')

        maxlen = max(
            [len(i) + len(j) for i, j in zip(self.__data.text, vals)])
        for txt, val in zip(self.__data.text, vals):
            offset = maxlen - len(txt) - len(val)
            self.__data.data.append(f'{txt}: {" " * offset}{val}')

    def __update_online(self) -> None:
        pass

    def __update_misc(self) -> None:
        pass

    def __back(self) -> None:
        self.fsm_back()

    def __filter(self, fltr: int) -> None:
        self.__data.fltr = fltr or 0
        self.__update_data()

    def __listclick(self, pos: int) -> None:
        pass
