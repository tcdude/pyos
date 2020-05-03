"""
Provides the Multiplayer Friends state.
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
class FriendsNodes:
    """Stores all relevant nodes for the Friends menu."""
    # pylint: disable=too-many-instance-attributes
    root: node.Node
    frame: frame.Frame
    listview: node.Node
    newview: node.Node
    userview: node.Node
    usertitle: label.Label
    usertxt: node.TextNode = None
    userremove: button.Button = None
    userchallenge: button.Button = None
    searchfield: entry.Entry = None
    searchbtn: button.Button = None
    cancelbtn: button.Button = None
    btnlist: buttonlist.ButtonList = None
    back: button.Button = None
    new: button.Button = None


@dataclass
class FriendsData:
    """Stores data used in the Friends menu."""
    data: List[str] = field(default_factory=list)
    fltr: int = None
    idmap: Dict[int, int] = field(default_factory=dict)
    active: int = None


@dataclass
class FriendsDlg:
    """Holds the different dialogue instances in the Friends menu."""
    replyrequest: Dialogue = None
    removerequest: Dialogue = None
    unblockrequest: Dialogue = None


class Friends(app.AppBase):
    """Friends view."""
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        root = self.ui.center.attach_node('MP Friends Root')
        _frame = frame.Frame('friends background', size=(0.9, 0.9),
                             frame_color=common.FRIENDS_FRAME_COLOR,
                             border_thickness=0.01, corner_radius=0.05,
                             multi_sampling=2)
        _frame.reparent_to(root)
        _frame.origin = Origin.CENTER
        listview = _frame.attach_node('MP Friends listview')
        fnt = self.config.get('font', 'bold')
        tit = label.Label(text='Friends', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt,
                          text_color=common.TITLE_TXT_COLOR, alpha=0)
        tit.reparent_to(listview)
        tit.origin = Origin.CENTER
        newview = _frame.attach_node('MP Friends newview')
        tit = label.Label(text='New Friend', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt,
                          text_color=common.TITLE_TXT_COLOR, alpha=0)
        tit.reparent_to(newview)
        tit.origin = Origin.CENTER
        newview.hide()
        userview = _frame.attach_node('MP Friends userview')
        tit = label.Label(text='Username', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt,
                          text_color=common.TITLE_TXT_COLOR, alpha=0)
        tit.reparent_to(userview)
        tit.origin = Origin.CENTER
        userview.hide()
        self.__nodes = FriendsNodes(root, _frame, listview, newview, userview,
                                    tit)
        self.__data = FriendsData()
        self.__dlgs = FriendsDlg()
        self.__setup()
        root.hide()

    def enter_friends(self):
        """Enter state -> Setup."""
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        self.__nodes.back.pos = pos_x, -0.38
        self.__nodes.new.pos = pos_x, 0.38
        self.__data.active = None
        self.__filter(self.__data.fltr)
        self.__update_data()
        self.__nodes.root.show()

    def exit_friends(self):
        """Exit state -> Setup."""
        if not self.__nodes.userview.hidden:
            self.__show_listview()
        self.__nodes.root.hide()
        if self.__dlgs.replyrequest is not None:
            self.__dlgs.replyrequest.hide()
        if self.__dlgs.removerequest is not None:
            self.__dlgs.removerequest.hide()
        if self.__dlgs.unblockrequest is not None:
            self.__dlgs.unblockrequest.hide()

    def __gen_dlg(self, dlg: str, txt: str) -> None:
        if dlg == 'reply':
            if self.__dlgs.replyrequest is None:
                fnt = self.config.get('font', 'bold')
                bkwa = common.get_dialogue_btn_kw(size=(0.11, 0.1))
                buttons = [DialogueButton(text=common.ACC_SYM, fmtkwargs=bkwa,
                                          callback=self.__accept_req),
                           DialogueButton(text=common.DEN_SYM, fmtkwargs=bkwa,
                                          callback=self.__deny_req),
                           DialogueButton(text=common.BLK_SYM, fmtkwargs=bkwa,
                                          callback=self.__block_req),
                           DialogueButton(text=common.BACK_SYM, fmtkwargs=bkwa,
                                          callback=self.__close_reply)]
                dlg = Dialogue(text=txt, buttons=buttons, margin=0.01,
                               size=(0.7, 0.7), font=fnt, align='center',
                               frame_color=common.FRIENDS_FRAME_COLOR,
                               border_thickness=0.01,
                               corner_radius=0.05, multi_sampling=2)
                dlg.pos = -0.35, -0.35
                dlg.reparent_to(self.ui.center)
                dlg.depth = 1000
                self.__dlgs.replyrequest = dlg
            else:
                self.__dlgs.replyrequest.text = txt
                self.__dlgs.replyrequest.show()
        elif dlg == 'remove':
            if self.__dlgs.removerequest is None:
                fnt = self.config.get('font', 'bold')
                bkwa = common.get_dialogue_btn_kw(size=(0.28, 0.1))
                buttons = [DialogueButton(text='Remove', fmtkwargs=bkwa,
                                          callback=self.__remove_req),
                           DialogueButton(text='Back', fmtkwargs=bkwa,
                                          callback=self.__close_remove)]
                dlg = Dialogue(text=txt, buttons=buttons, margin=0.01,
                               size=(0.7, 0.7), font=fnt, align='center',
                               frame_color=common.FRIENDS_FRAME_COLOR,
                               border_thickness=0.01,
                               corner_radius=0.05, multi_sampling=2)
                dlg.pos = -0.35, -0.35
                dlg.reparent_to(self.ui.center)
                dlg.depth = 1000
                self.__dlgs.removerequest = dlg
            else:
                self.__dlgs.removerequest.text = txt
                self.__dlgs.removerequest.show()
        elif dlg == 'unblock':
            if self.__dlgs.unblockrequest is None:
                fnt = self.config.get('font', 'bold')
                bkwa = common.get_dialogue_btn_kw(size=(0.11, 0.1))
                buttons = [DialogueButton(text=common.ACC_SYM, fmtkwargs=bkwa,
                                          callback=self.__unblock,
                                          cbargs=(True, )),
                           DialogueButton(text=common.DEN_SYM, fmtkwargs=bkwa,
                                          callback=self.__unblock,
                                          cbargs=(False, )),
                           DialogueButton(text=common.BACK_SYM, fmtkwargs=bkwa,
                                          callback=self.__close_unblock)]
                dlg = Dialogue(text=txt, buttons=buttons, margin=0.01,
                               size=(0.7, 0.7), font=fnt, align='center',
                               frame_color=common.FRIENDS_FRAME_COLOR,
                               border_thickness=0.01,
                               corner_radius=0.05, multi_sampling=2)
                dlg.pos = -0.35, -0.35
                dlg.reparent_to(self.ui.center)
                dlg.depth = 1000
                self.__dlgs.unblockrequest = dlg
            else:
                self.__dlgs.unblockrequest.text = txt
                self.__dlgs.unblockrequest.show()

    def __unblock(self, decision: bool) -> None:
        self.__dlgs.unblockrequest.hide()
        self.statuslbl.show()
        self.statuslbl.text = 'Unblocking user...'
        userid = self.__data.idmap[self.__data.active]
        req = self.mps.ctrl.unblock_user(userid, decision)
        self.mps.ctrl.register_callback(req, self.__unblock_req)
        self.__data.active = None

    def __unblock_req(self, rescode: int) -> None:
        if rescode:
            logger.warning(f'Request failed {mpctrl.RESTXT[rescode]}')
        self.statuslbl.hide()
        self.__show_listview()

    def __close_unblock(self) -> None:
        self.__data.active = None
        self.__dlgs.unblockrequest.hide()

    def __accept_req(self) -> None:
        self.__dlgs.replyrequest.hide()
        userid = self.__data.idmap[self.__data.active]
        req = self.mps.ctrl.reply_friend_request(userid, True)
        self.mps.ctrl.register_callback(req, self.__reqcb)
        self.statuslbl.text = 'Sending reply...'
        self.statuslbl.show()
        self.__data.active = None

    def __deny_req(self) -> None:
        self.__dlgs.replyrequest.hide()
        userid = self.__data.idmap[self.__data.active]
        req = self.mps.ctrl.remove_friend(userid)
        self.mps.ctrl.register_callback(req, self.__reqcb)
        self.statuslbl.text = 'Sending reply...'
        self.statuslbl.show()
        self.__data.active = None

    def __block_req(self) -> None:
        self.__dlgs.replyrequest.hide()
        userid = self.__data.idmap[self.__data.active]
        req = self.mps.ctrl.reply_friend_request(userid, False)
        self.mps.ctrl.register_callback(req, self.__reqcb)
        self.statuslbl.text = 'Sending reply...'
        self.statuslbl.show()
        self.__data.active = None

    def __close_reply(self) -> None:
        self.__dlgs.replyrequest.hide()
        self.__data.active = None

    def __remove_req(self) -> None:
        self.__dlgs.removerequest.hide()
        userid = self.__data.idmap[self.__data.active]
        req = self.mps.ctrl.remove_friend(userid)
        self.mps.ctrl.register_callback(req, self.__reqcb)
        self.statuslbl.text = 'Sending reply...'
        self.statuslbl.show()
        self.__data.active = None

    def __close_remove(self) -> None:
        self.__dlgs.removerequest.hide()
        if self.__nodes.userview.hidden:
            self.__data.active = None

    def __reqcb(self, rescode: int) -> None:
        self.statuslbl.hide()
        if rescode:
            logger.warning(f'Request failed {mpctrl.RESTXT[rescode]}')
            return
        if not self.__nodes.userview.hidden:
            self.__show_listview()
            return
        self.__update_data()

    def __update_data(self) -> None:
        req = self.mps.ctrl.sync_relationships()
        self.mps.ctrl.register_callback(req, self.__sync_relcb)
        self.statuslbl.text = 'Updating Friends...'
        self.statuslbl.show()
        self.__nodes.back.enabled = False

    def __sync_relcb(self, rescode: int) -> None:
        self.statuslbl.hide()
        self.__nodes.back.enabled = True
        if rescode:
            logger.warning(f'Unable to sync relationships '
                           f'"{mpctrl.RESTXT[rescode]}"')
            return
        self.__data.data.clear()
        self.__data.idmap.clear()
        if self.__data.fltr == 0:
            data = self.mps.dbh.friends
            data.sort()
        elif self.__data.fltr == 1:
            data = self.mps.dbh.pending
            data.sort(key=lambda x: x[1:])
        elif self.__data.fltr == 2:
            data = self.mps.dbh.blocked
            data.sort()
        for i, (user_id, username) in enumerate(data):
            if self.__data.fltr == 1:
                if username.startswith('i'):
                    self.__data.data.append(f'{common.IN_SYM} {username[1:]}')
                else:
                    self.__data.data.append(f'{common.OUT_SYM} {username[1:]}')
            else:
                self.__data.data.append(username)
            self.__data.idmap[i] = user_id
        self.__nodes.btnlist.update_content(True)

    def __setup(self):
        # listview
        fnt = self.config.get('font', 'bold')
        self.__nodes.btnlist = common \
            .gen_btnlist(self.config.get('font', 'normal'), fnt,
                         self.__data.data, (self.__listclick, self.__filter), 4,
                         (0.85, 0.625), self.__nodes.listview,
                         ['Friends', 'Pending', 'Blocked'])
        self.__nodes.btnlist.pos = 0, 0
        kwargs = common.get_menu_sym_btn_kw()
        self.__nodes.new = button.Button(name='new button', pos=(0, 0.38),
                                         text=common.NEW_SYM, **kwargs)
        self.__nodes.new.origin = Origin.CENTER
        self.__nodes.new.reparent_to(self.__nodes.listview)
        self.__nodes.new.onclick(self.__new_friend)

        # always visible
        self.__nodes.back = button.Button(name='back button',
                                          pos=(0, -0.38),
                                          text=common.BACK_SYM,
                                          **kwargs)
        self.__nodes.back.origin = Origin.CENTER
        self.__nodes.back.reparent_to(self.__nodes.frame)
        self.__nodes.back.onclick(self.__back)

        # newview
        self.__nodes.searchfield = entry.Entry(name='friendsearch',
                                               size=(0.8, 0.1),
                                               pos=(-0.4, -0.195),
                                               hint_text='Search User',
                                               **common.get_entry_kw())
        self.__nodes.searchfield.reparent_to(self.__nodes.newview)
        self.__nodes.searchfield.onenter(self.__find_user)
        self.__nodes.searchbtn = button.Button(name='friendsearchbtn',
                                               text='Send Request',
                                               pos=(-0.08, -0.05),
                                               **common.get_dialogue_btn_kw(
                                                   size=(0.5, 0.1)))
        self.__nodes.searchbtn.reparent_to(self.__nodes.newview)
        self.__nodes.searchbtn.onclick(self.__find_user)
        self.__nodes.cancelbtn = button.Button(name='friendcancelbtn',
                                               text='Cancel',
                                               pos=(-0.4, -0.05),
                                               **common.get_dialogue_btn_kw(
                                                   size=(0.3, 0.1)))
        self.__nodes.cancelbtn.reparent_to(self.__nodes.newview)
        self.__nodes.cancelbtn.onclick(self.__show_listview)

        # userview
        self.__nodes.usertxt = self.__nodes.userview \
            .attach_text_node(text='Username', align='center', font_size=0.05,
                              font=fnt, text_color=common.TITLE_TXT_COLOR,
                              alpha=0, multiline=True, pos=(0, -0.1))
        self.__nodes.usertxt.origin = Origin.CENTER
        kwa = common.get_dialogue_btn_kw(size=(0.32, 0.1))
        self.__nodes.userchallenge = button \
            .Button(text='Challenge', pos=(-0.35, 0.25), **kwa)
        self.__nodes.userchallenge.reparent_to(self.__nodes.userview)
        self.__nodes.userchallenge.onclick(self.__start_challenge)
        self.__nodes.userremove = button \
            .Button(text='Remove', pos=(0.03, 0.25), **kwa)
        self.__nodes.userremove.reparent_to(self.__nodes.userview)
        self.__nodes.userremove.onclick(self.__remove_friend)

    def __back(self) -> None:
        logger.debug(f'back nodeid {self.__nodes.back.node_id}')
        if self.__nodes.listview.hidden:
            self.__show_listview()
        else:
            self.fsm_back()

    def __show_listview(self) -> None:
        self.__data.active = None
        self.__nodes.newview.hide()
        self.__nodes.userview.hide()
        self.__nodes.listview.show()
        self.__update_data()

    def __find_user(self) -> None:
        username = self.__nodes.searchfield.text
        if not 2 < len(username) < 31:
            return
        req = self.mps.ctrl.friend_request(username)
        self.mps.ctrl.register_callback(req, self.__friendreqcb)
        self.statuslbl.text = 'Sending request...'

    def __friendreqcb(self, rescode: int) -> None:
        self.statuslbl.hide()
        if rescode == 0:
            self.__show_listview()

    def __new_friend(self) -> None:
        self.__nodes.listview.hide()
        self.__nodes.newview.show()
        self.__nodes.searchfield.text = ''

    def __filter(self, fltr: int = None) -> None:
        self.__data.fltr = fltr or 0
        self.__update_data()

    def __listclick(self, pos: int) -> None:
        self.__data.active = pos
        if self.__data.fltr == 1:
            if self.__data.data[pos].startswith(common.IN_SYM):
                txt = f'Friendrequest\n{self.__data.data[pos]}\n\n' \
                    f'{common.ACC_SYM} Accept {common.DEN_SYM} Deny\n' \
                    f'{common.BLK_SYM} Block or {common.BACK_SYM} Back\n\n'
                self.__gen_dlg('reply', txt)
            else:
                txt = 'Remove pending\nfriendrequest?\n\n'
                self.__gen_dlg('remove', txt)
            return
        if self.__data.fltr == 2:
            txt = f'Unblock user\n{self.__data.data[pos]}\n\n' \
                f'{common.ACC_SYM} Become Friends\n{common.DEN_SYM} Remove\n' \
                f'or {common.BACK_SYM} Back\n\n'
            self.__gen_dlg('unblock', txt)
            return
        self.__nodes.usertitle.text = self.__data.data[pos]
        userid = self.__data.idmap[pos]
        if self.mps.dbh.canchallenge(userid):
            self.__nodes.userchallenge.enabled = True
        else:
            self.__nodes.userchallenge.enabled = False
        req = self.mps.ctrl.challenge_stats(userid)
        self.mps.ctrl.register_callback(req, self.__gen_userstat)
        self.statuslbl.show()
        self.statuslbl.text = 'Loading user stats...'

    def __start_challenge(self) -> None:
        # TODO: Launch start challenge dialogue from Challenges state
        pass

    def __remove_friend(self) -> None:
        username = self.__data.data[self.__data.active]
        self.__gen_dlg('remove', f'Remove friend\n{username} ?\n\n')

    def __gen_userstat(self, unused_rescode: int) -> None:
        self.statuslbl.hide()
        self.__nodes.listview.hide()
        self.__nodes.userview.show()
        values = self.mps.dbh \
            .userstats(self.__data.idmap[self.__data.active])
        txt = ['Rank ', 'Points ', 'Rounds won ', 'Rounds lost ',
               'Rounds draw ']
        numlen = len(str(max(values)))
        txtlen = [len(i) for i in txt]
        txtmax = max(txtlen) + numlen
        msg = ''
        for desc, value, tlen in zip(txt, values, txtlen):
            val = str(value)
            padding = txtmax - len(val) - tlen
            msg += desc + ' ' * padding + val + '\n'
        self.__nodes.usertxt.text = msg
