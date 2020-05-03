"""
Provides the Multiplayer Challenge State.
"""
# pylint: disable=too-many-lines

from dataclasses import dataclass, field
from typing import Dict, List

from foolysh.scene import node
from foolysh.scene.node import Origin
from foolysh.ui import button, frame, entry, label
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


@dataclass
class ChallengesNodes:
    """Stores all relevant nodes for the Challenges menu."""
    # pylint: disable=too-many-instance-attributes
    root: node.Node
    frame: frame.Frame
    listview: node.Node
    newview: node.Node
    challengeview: node.Node
    challengetitle: label.Label
    challengetxt: node.TextNode = None
    userremove: button.Button = None
    userchallenge: button.Button = None
    searchfield: entry.Entry = None
    searchbtn: button.Button = None
    cancelbtn: button.Button = None
    btnlist: buttonlist.ButtonList = None
    newviewbtnlist: buttonlist.ButtonList = None
    back: button.Button = None
    new: button.Button = None


@dataclass
class ChallengesData:
    """Stores data used in the Challenges menu."""
    data: List[str] = field(default_factory=list)
    fltr: int = None
    idmap: Dict[int, int] = field(default_factory=dict)
    active: int = None


@dataclass
class ChallengesDlg:
    """Holds the different dialogue instances in the Challenges menu."""
    newchallenge: Dialogue = None


class Challenges(app.AppBase):
    """Challenges view."""
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        root = self.ui.center.attach_node('MP Challenges Root')
        _frame = frame.Frame('challenges background', size=(0.9, 0.9),
                             frame_color=common.CHALLENGES_FRAME_COLOR,
                             border_thickness=0.01, corner_radius=0.05,
                             multi_sampling=2)
        _frame.reparent_to(root)
        _frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        listview = _frame.attach_node('MP Challenges listview')
        tit = label.Label(text='Challenges', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt,
                          text_color=common.TITLE_TXT_COLOR, alpha=0)
        tit.reparent_to(listview)
        tit.origin = Origin.CENTER

        newview = _frame.attach_node('MP Challenges newview')
        tit = label.Label(text='Start Challenge', align='center', font=fnt,
                          size=(0.8, 0.1), pos=(0, -0.4), font_size=0.06,
                          text_color=common.TITLE_TXT_COLOR, alpha=0)
        tit.reparent_to(newview)
        tit.origin = Origin.CENTER
        newview.hide()

        challengeview = _frame.attach_node('MP Challenges challengeview')
        tit = label.Label(text='', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt,
                          text_color=common.TITLE_TXT_COLOR, alpha=0)
        tit.reparent_to(challengeview)
        tit.origin = Origin.CENTER
        challengeview.hide()
        self.__nodes = ChallengesNodes(root, _frame, listview, newview,
                                       challengeview, tit)
        self.__data = ChallengesData()
        self.__dlgs = ChallengesDlg()
        self.__setup()
        root.hide()

    def enter_challenges(self):
        """Enter state -> Setup."""
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        self.__nodes.back.pos = pos_x, -0.38
        self.__nodes.new.pos = pos_x, 0.38
        self.__filter(self.__data.fltr)
        self.__nodes.btnlist.update_content()
        self.__nodes.root.show()

    def exit_challenges(self):
        """Exit state -> Setup."""
        self.__nodes.root.hide()
        if self.__dlgs.newchallenge is not None:
            self.__dlgs.newchallenge.hide()

    def __update_list(self) -> None:
        req = self.mps.ctrl.sync_challenges()
        self.mps.ctrl.register_callback(req, self.__update_listcb)
        self.statuslbl.show()
        self.statuslbl.text = 'Updating Challenges...'

    def __update_listcb(self, rescode: int) -> None:
        self.statuslbl.hide()
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
        self.__data.data.clear()
        self.__data.idmap.clear()
        if self.__data.fltr == 0:
            data = self.mps.dbh.chmyturn
        elif self.__data.fltr == 1:
            data = self.mps.dbh.chwaiting
        elif self.__data.fltr == 2:
            data = self.mps.dbh.chfinished
        for i, (challenge_id, txt) in enumerate(data):
            self.__data.data.append(txt)
            self.__data.idmap[i] = challenge_id
        self.__nodes.btnlist.update_content(True)

    def __gen_dlg(self, dlg: str, txt: str) -> None:
        if dlg == 'new':
            if self.__dlgs.newchallenge is None:
                fnt = self.config.get('font', 'bold')
                bkwa = common.get_dialogue_btn_kw(size=(0.11, 0.11))
                buttons = [DialogueButton(text='1', fmtkwargs=bkwa,
                                          callback=self.__challenge_req,
                                          cbargs=(1, )),
                           DialogueButton(text='3', fmtkwargs=bkwa,
                                          callback=self.__challenge_req,
                                          cbargs=(3, )),
                           DialogueButton(text='5', fmtkwargs=bkwa,
                                          callback=self.__challenge_req,
                                          cbargs=(5, )),
                           DialogueButton(text='7', fmtkwargs=bkwa,
                                          callback=self.__challenge_req,
                                          cbargs=(7, )),
                           DialogueButton(text=common.BACK_SYM, fmtkwargs=bkwa,
                                          callback=self.__back)]
                dlg = Dialogue(text=txt, buttons=buttons, margin=0.01,
                               size=(0.7, 0.7), font=fnt, align='center',
                               frame_color=common.CHALLENGES_FRAME_COLOR,
                               border_thickness=0.01,
                               corner_radius=0.05, multi_sampling=2)
                dlg.pos = -0.35, -0.35
                dlg.reparent_to(self.ui.center)
                dlg.depth = 1000
                self.__dlgs.newchallenge = dlg
            else:
                self.__dlgs.newchallenge.text = txt
                self.__dlgs.newchallenge.show()

    def __challenge_req(self, rounds: int) -> None:
        self.__dlgs.newchallenge.hide()
        userid = self.__data.idmap[self.__data.active]
        req = self.mps.ctrl.start_challenge(userid, rounds)
        self.mps.ctrl.register_callback(req, self.__challenge_reqcb)
        self.statuslbl.show()
        self.statuslbl.text = 'Sending request...'

    def __challenge_reqcb(self, rescode: int) -> None:
        self.statuslbl.hide()
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
        self.__update_new_list()

    def __setup(self):
        # always visible
        kwargs = common.get_menu_sym_btn_kw()
        self.__nodes.back = button.Button(name='back button', pos=(0, -0.38),
                                          text=common.BACK_SYM, **kwargs)
        self.__nodes.back.origin = Origin.CENTER
        self.__nodes.back.reparent_to(self.__nodes.frame)
        self.__nodes.back.onclick(self.__back)

        # listview
        self.__nodes.btnlist = common \
            .gen_btnlist(self.config.get('font', 'normal'),
                         self.config.get('font', 'bold'), self.__data.data,
                         (self.__listclick, self.__filter), 4, (0.85, 0.625),
                         self.__nodes.listview, ['My Turn', 'Waiting',
                                                 'Finished'])
        self.__nodes.new = button.Button(name='new button', pos=(0, 0.38),
                                         text=common.NEW_SYM, **kwargs)
        self.__nodes.new.origin = Origin.CENTER
        self.__nodes.new.reparent_to(self.__nodes.listview)
        self.__nodes.new.onclick(self.__new_challenge)

        # newview
        self.__nodes.newviewbtnlist = common \
            .gen_btnlist(self.config.get('font', 'normal'),
                         self.config.get('font', 'bold'), self.__data.data,
                         (self.__listclick, None), 8, (0.85, 0.7),
                         self.__nodes.newview)
        self.__nodes.newviewbtnlist.pos = 0, 0.06

    def __back(self):
        dlgs = (self.__dlgs.newchallenge, )
        for i in dlgs:
            if i is not None and not i.hidden:
                i.hide()
                return
        if self.__nodes.listview.hidden:
            self.__show_listview()
            return
        self.request('multiplayer_menu')

    def __show_listview(self) -> None:
        self.__nodes.newview.hide()
        self.__nodes.challengeview.hide()
        self.__nodes.listview.show()
        self.__update_list()

    def __new_challenge(self):
        self.__nodes.listview.hide()
        self.__nodes.newview.show()
        self.__update_new_list()

    def __update_new_list(self) -> None:
        req = self.mps.ctrl.sync_relationships()
        self.mps.ctrl.register_callback(req, self.__update_new_listcb)
        self.statuslbl.show()
        self.statuslbl.text = 'Updating Friends...'

    def __update_new_listcb(self, rescode: int) -> None:
        self.statuslbl.hide()
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
        data = self.mps.dbh.challenge_available
        self.__data.data.clear()
        self.__data.idmap.clear()
        for i, (user_id, username) in enumerate(data):
            self.__data.data.append(username)
            self.__data.idmap[i] = user_id
        self.__nodes.newviewbtnlist.update_content(True)

    def __filter(self, fltr: int = None) -> None:
        self.__data.fltr = fltr or 0
        self.__update_list()

    def __listclick(self, pos: int) -> None:
        self.__data.active = pos
        if not self.__nodes.listview.hidden:
            print(f'listview clicked on "{self.__data.data[pos]}"')
            return
        if not self.__nodes.newview.hidden:
            print(f'newview clicked on "{self.__data.data[pos]}"')
            self.__gen_dlg('new', f'Select the number\nof rounds to play\n'
                                  f'or {common.BACK_SYM} to go back.\n\n')
            return
        # TODO: Handle click
