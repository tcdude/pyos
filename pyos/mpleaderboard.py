"""
Provides the Multiplayer Leaderboard state.
"""
# pylint: disable=too-many-lines

from dataclasses import dataclass
from typing import Dict, List, Tuple

from foolysh.scene.node import Origin
from foolysh.ui import button, frame, label
from loguru import logger

import app
import buttonlist
import common
from dialogue import Dialogue, DialogueButton
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

ITPP = 8  # Items per page


@dataclass
class LeaderboardDialogues:
    """Holds dialogues for the leaderboard state."""
    friendreq: Dialogue = None

    @property
    def all(self) -> Tuple[Dialogue, ...]:
        """All dialogues as tuple."""
        return (self.friendreq, )


class Leaderboard(app.AppBase):
    """Leaderboard view."""
    # pylint: disable=too-many-instance-attributes
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__root = self.ui.center.attach_node('MP Leaderboard Root')
        self.__frame = frame.Frame('leaderboard background', size=(0.9, 0.9),
                                   frame_color=common.LEADERBOARD_FRAME_COLOR,
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2, parent=self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = label.Label(text='Leaderboard', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt, alpha=0,
                          text_color=common.TITLE_TXT_COLOR,
                          parent=self.__frame)
        tit.origin = Origin.CENTER
        self.__data: List[str] = []
        self.__idmap: Dict[int, int] = {}
        self.__btnlist: buttonlist.ButtonList = None
        self.__dlgs: LeaderboardDialogues = LeaderboardDialogues()
        self.__active: int = None
        self.__back: button.Button = None
        self.__setup()
        self.__root.hide()

    def enter_leaderboard(self):
        """Enter state -> Setup."""
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        self.__back.pos = pos_x, -0.38
        self.__update_data()
        self.__root.show()

    def exit_leaderboard(self):
        """Exit state -> Setup."""
        self.__root.hide()

    def __update_data(self, page: int = None) -> None:
        if page is None:
            req = self.mps.ctrl.update_leaderboard(0, 2 * ITPP)
            reset = True
        else:
            start = page * ITPP
            req = self.mps.ctrl.update_leaderboard(start, start + 2 * ITPP)
            reset = False
        self.mps.ctrl.register_callback(req, self.__update_datacb, reset)
        self.global_nodes.show_status('Updating Leaderboard...')

    def __update_datacb(self, rescode: int, reset_page: bool) -> None:
        self.global_nodes.hide_status()
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
        else:
            self.__data.clear()
            ranklen = 1
            rankmax = self.mps.dbh.rankmax
            limit = 10
            while rankmax >= limit:
                ranklen += 1
                limit *= 10
            user = self.config.get('mp', 'user')
            for i, (rank, points, name) in enumerate(self.mps.dbh.leaderboard):
                if name == user:
                    self.__idmap[i] = -1, None
                else:
                    self.__idmap[i] = rank, name
                rank = str(rank)
                pad = ranklen - len(rank)
                self.__data.append(' ' * pad + f'{rank}. {points} {name}')
        self.__btnlist.update_content(reset_page)

    def __gen_dlg(self, dlg: str, txt: str) -> None:
        if dlg == 'friendreq':
            if self.__dlgs.friendreq is None:
                fnt = self.config.get('font', 'bold')
                bkwa = common.get_dialogue_btn_kw(size=(0.2, 0.1))
                buttons = [DialogueButton(text='Yes', fmtkwargs=bkwa,
                                          callback=self.__friendreq),
                           DialogueButton(text='No', fmtkwargs=bkwa,
                                          callback=self.__close_dlg)]
                dlg = Dialogue(text=txt, buttons=buttons, margin=0.01,
                               size=(0.7, 0.7), font=fnt, align='center',
                               frame_color=common.LEADERBOARD_FRAME_COLOR,
                               border_thickness=0.01, parent=self.ui.center,
                               corner_radius=0.05, multi_sampling=2)
                dlg.pos = -0.35, -0.35
                dlg.depth = 1000
                self.__dlgs.friendreq = dlg
            else:
                self.__dlgs.friendreq.text = txt
                self.__dlgs.friendreq.show()

    def __setup(self):
        self.__btnlist = common \
            .gen_btnlist(self.config.get('font', 'normal'),
                         self.config.get('font', 'bold'), self.__data,
                         (self.__listclick, None), ITPP, (0.85, 0.7),
                         self.__frame, item_align='left')
        self.__btnlist.onpagechange(self.__pagechange)
        self.__btnlist.pos = 0, 0.06
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        kwargs = common.get_menu_sym_btn_kw()
        self.__back = button.Button(name='back button', pos=(pos_x, -0.38),
                                    text=common.BACK_SYM, parent=self.__frame,
                                    **kwargs)
        self.__back.origin = Origin.CENTER
        self.__back.onclick(self.__back_pressed)

    def __back_pressed(self) -> None:
        if self.__close_dlg():
            return
        self.request('multiplayer_menu')

    def __friendreq(self) -> None:
        req = self.mps.ctrl.friend_request(self.__idmap[self.__active][1])
        self.mps.ctrl.register_callback(req, self.__friendreqcb)
        self.global_nodes.show_status('Sending friend request...')

    def __friendreqcb(self, rescode: int) -> None:
        self.global_nodes.hide_status()
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
        self.__close_dlg()

    def __close_dlg(self) -> bool:
        self.__active = None
        for i in self.__dlgs.all:
            if i is not None and not i.hidden:
                i.hide()
                return True
        return False

    def __pagechange(self, page: int) -> int:
        self.__update_data(page)
        return page

    def __listclick(self, pos: int) -> None:
        if self.__idmap[pos][0] < 1:
            logger.debug('Clicked on user')
            return
        userid = self.mps.dbh.userid(self.__idmap[pos][1])
        if userid == -3:
            self.__active = pos
            self.__gen_dlg('friendreq', f'Do you want to send\na friend '
                                        f'request to:\n{self.__idmap[pos][1]} ?'
                                        f'\n\n\n')
