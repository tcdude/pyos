"""
Provides the different menus in the app.
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

NOACCTXT = """No online account
configured.
Go to settings """ + chr(0xf178) + ' ' + chr(0xf013) + """
in the multiplayer
menu and enter your
account info.


"""

UNCHANGED = chr(255) * 8


@dataclass
class MenuButtons:
    """Buttons of the multiplayer menu."""
    challenges: button.Button
    leaderboard: button.Button
    friends: button.Button
    settings: button.Button
    back: button.Button


class MultiplayerMenu(app.AppBase):
    """Multiplayer menu."""
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__root = self.ui.center.attach_node('MP Menu Root')
        self.__frame = frame.Frame('multiplayer background', size=(0.9, 0.9),
                                   frame_color=common.FRAME_COLOR_STD,
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2)
        self.__frame.reparent_to(self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = label.Label(text='Multiplayer', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt,
                          text_color=common.TITLE_TXT_COLOR, alpha=0)
        tit.reparent_to(self.__frame)
        tit.origin = Origin.CENTER
        self.__buttons: MenuButtons = None
        self.__setup_menu_buttons()
        self.__dlg: Dialogue = None
        self.__root.hide()

    def enter_multiplayer_menu(self):
        """Enter state -> Setup."""
        logger.debug('Enter Multiplayer Menu')
        if not self.mps.ctrl.active:
            self.mps.ctrl.start_service()
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        self.__buttons.settings.pos = pos_x, 0.38
        self.__buttons.back.pos = pos_x, -0.38
        if self.mps.login != 0:
            if 'dlg_shown' not in self.fsm_data and self.mps.ctrl.noaccount:
                self.__gen_dlg(NOACCTXT)
                self.fsm_data['dlg_shown'] = True
            elif self.mps.login > 0:
                self.__gen_dlg(f'Unable to connect\n\n'
                               f'{mpctrl.RESTXT[self.mps.login]}\n\n\n')
            self.__buttons.challenges.enabled = False
            self.__buttons.friends.enabled = False
            self.__buttons.leaderboard.enabled = False
        else:
            self.__buttons.challenges.enabled = True
            self.__buttons.friends.enabled = True
            self.__buttons.leaderboard.enabled = True
        self.__buttons.back.enabled = False
        self.__update_notifications()
        self.__root.show()

    def exit_multiplayer_menu(self):
        """Exit state -> Setup."""
        logger.debug('Exit Multiplayer Menu')
        self.__root.hide()
        if self.__dlg is not None:
            self.__dlg.hide()

    def __update_notifications(self) -> None:
        self.__buttons.back.enabled = False
        req = self.mps.ctrl.nop()
        self.mps.ctrl.register_callback(req, self.__enable_back)

    def __enable_back(self, unused_rescode: int) -> None:
        self.__buttons.back.enabled = True

    def __hide_dlg(self):
        self.__dlg.hide()
        self.__frame.show()

    def __gen_dlg(self, txt: str, align: str = 'center'):
        if self.__dlg is None:
            fnt = self.config.get('font', 'bold')
            buttons = [DialogueButton(text='Ok',
                                      fmtkwargs=common.get_dialogue_btn_kw(),
                                      callback=self.__hide_dlg)]
            dlg = Dialogue(text=txt, buttons=buttons, margin=0.01,
                           size=(0.7, 0.7), font=fnt, align=align,
                           frame_color=common.FRAME_COLOR_STD,
                           border_thickness=0.01,
                           corner_radius=0.05, multi_sampling=2)
            dlg.pos = -0.35, -0.35
            dlg.reparent_to(self.ui.center)
            dlg.depth = 1000
            self.__dlg = dlg
        else:
            self.__dlg.text = txt
            self.__dlg.align = align
            self.__dlg.show()
        self.__frame.hide()

    def __setup_menu_buttons(self):
        kwargs = common.get_menu_txt_btn_kw(size=(0.8, 0.1))
        offset = 0.125
        pos_y = -0.1
        txt = chr(0xf9e4) + '  Challenges  ' + chr(0xf9e4)
        challenges = button.Button(name='challenges button', pos=(0, pos_y),
                                   text=txt,
                                   **kwargs)
        challenges.origin = Origin.CENTER
        challenges.reparent_to(self.__frame)
        challenges.onclick(self.request, 'challenges')
        pos_y += offset
        txt = chr(0xfa39) + ' Leaderboard ' + chr(0xfa39)
        leaderboard = button.Button(name='leaderboard button', pos=(0, pos_y),
                                    text=txt, **kwargs)
        leaderboard.origin = Origin.CENTER
        leaderboard.reparent_to(self.__frame)
        leaderboard.onclick(self.request, 'leaderboard')
        pos_y += offset
        txt = chr(0xf0c0) + ' ' * 3 + 'Friends' + ' ' * 3 + chr(0xf0c0)
        friends = button.Button(name='friends button', pos=(0, pos_y),
                                text=txt, **kwargs)
        friends.origin = Origin.CENTER
        friends.reparent_to(self.__frame)
        friends.onclick(self.request, 'friends')
        pos_y += offset
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        kwargs = common.get_menu_sym_btn_kw()
        settings = button.Button(name='settings button', pos=(pos_x, 0.38),
                                 text=chr(0xf013), **kwargs)
        settings.origin = Origin.CENTER
        settings.reparent_to(self.__frame)
        settings.onclick(self.request, 'multiplayer_settings')
        back = button.Button(name='back button', pos=(pos_x, -0.38),
                             text=common.BACK_SYM, **kwargs)
        back.origin = Origin.CENTER
        back.reparent_to(self.__frame)
        back.onclick(self.__back)
        self.__buttons = MenuButtons(challenges, leaderboard, friends, settings,
                                     back)

    def __back(self) -> None:
        logger.debug(f'back nodeid {self.__buttons.back.node_id}')
        logger.debug('MP Menu Back clicked')
        self.request('main_menu')

def _gen_btnlist(item_font: str, filter_font: str, data: List[str],
                 cbs: Tuple[Callable, Callable], itpp: int,
                 size: Tuple[float, float], parent: object = None,
                 filters: List[str] = None):
    # pylint: disable=too-many-arguments
    kwargs = {'font': item_font, 'text_color': (0, 50, 0, 255),
              'frame_color': (200, 220, 200),
              'down_text_color': (255, 255, 255, 255),
              'border_thickness': 0.005, 'down_border_thickness': 0.008,
              'border_color': (0, 50, 0), 'down_border_color': (255, 255, 255),
              'corner_radius': 0.025, 'multi_sampling': 2, 'align': 'center'}
    fkwargs = {}
    fkwargs.update(kwargs)
    fkwargs['size'] = 0.25, 0.08
    fkwargs['font'] = filter_font
    fkwargs['border_color'] = (200, ) * 3
    return buttonlist.ButtonList(data, cbs[0], itpp, kwargs, parent, filters,
                                 cbs[1], fkwargs, (0, 50, 0), size=size,
                                 frame_color=common.BTNLIST_FRAME_COLOR,
                                 border_color=common.BTNLIST_BORDER_COLOR,
                                 border_thickness=0.005, corner_radius=0.03,
                                 multi_sampling=2)


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
        self.__btnlist = _gen_btnlist(self.config.get('font', 'normal'),
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
        elif self.__data.fltr == 1:
            data = self.mps.dbh.pending
        elif self.__data.fltr == 2:
            data = self.mps.dbh.blocked
        for i, (user_id, username) in enumerate(data):
            if self.__data.fltr == 1:
                if username.startswith('i'):
                    self.__data.data.append(f'{common.IN_SYM} {username[1:]}')
                else:
                    self.__data.data.append(f'{common.OUT_SYM} {username[1:]}')
            else:
                self.__data.data.append(username)
            self.__data.idmap[i] = user_id
        if self.__data.fltr == 1:
            self.__data.data.sort(key=lambda x: x[2:])
        else:
            self.__data.data.sort()
        self.__nodes.btnlist.update_content(True)

    def __setup(self):
        # listview
        fnt = self.config.get('font', 'bold')
        self.__nodes.btnlist = _gen_btnlist(self.config.get('font', 'normal'),
                                            fnt, self.__data.data,
                                            (self.__listclick, self.__filter),
                                            4, (0.85, 0.625),
                                            self.__nodes.listview,
                                            ['Friends', 'Pending', 'Blocked'])
        self.__nodes.btnlist.pos = 0, 0
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        kwargs = common.get_menu_sym_btn_kw()
        self.__nodes.new = button.Button(name='new button', pos=(pos_x, 0.38),
                                         text=chr(0xf893), **kwargs)
        self.__nodes.new.origin = Origin.CENTER
        self.__nodes.new.reparent_to(self.__nodes.listview)
        self.__nodes.new.onclick(self.__new_friend)

        # always visible
        self.__nodes.back = button.Button(name='back button',
                                          pos=(pos_x, -0.38),
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


class Leaderboard(app.AppBase):
    """Leaderboard view."""
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__root = self.ui.center.attach_node('MP Leaderboard Root')
        self.__frame = frame.Frame('leaderboard background', size=(0.9, 0.9),
                                   frame_color=common.LEADERBOARD_FRAME_COLOR,
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2)
        self.__frame.reparent_to(self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = label.Label(text='Leaderboard', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt,
                          text_color=common.TITLE_TXT_COLOR, alpha=0)
        tit.reparent_to(self.__frame)
        tit.origin = Origin.CENTER
        self.__data: List[str] = []
        self.__btnlist: buttonlist.ButtonList = None
        self.__back: button.Button = None
        self.__setup_menu_buttons()
        self.__root.hide()

    def enter_leaderboard(self):
        """Enter state -> Setup."""
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        self.__back.pos = pos_x, -0.38
        self.__btnlist.update_content()
        self.__root.show()

    def exit_leaderboard(self):
        """Exit state -> Setup."""
        self.__root.hide()

    def __setup_menu_buttons(self):
        self.__btnlist = _gen_btnlist(self.config.get('font', 'normal'),
                                      self.config.get('font', 'bold'),
                                      self.__data, (self.__listclick, None), 8,
                                      (0.85, 0.7), self.__frame)
        self.__data += [
            str(i + 1) + '. 123456 ' + chr(i%26+65) * 32 for i in range(200)]
        self.__btnlist.pos = 0, 0.06
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        kwargs = common.get_menu_sym_btn_kw()
        self.__back = button.Button(name='back button', pos=(pos_x, -0.38),
                                    text=common.BACK_SYM, **kwargs)
        self.__back.origin = Origin.CENTER
        self.__back.reparent_to(self.__frame)
        self.__back.onclick(self.request, 'multiplayer_menu')

    def __listclick(self, pos: int) -> None:
        print(f'clicked on "{self.__data[pos]}"')
        # TODO: Open Challenge Dialogue


class MultiplayerSettings(app.AppBase):
    """MultiplayerSettings view."""
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__root = self.ui.center.attach_node('MP Settings Root')
        self.__frame = frame.Frame('mp settings background', size=(0.9, 0.9),
                                   frame_color=common.SETTINGS_FRAME_COLOR,
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2)
        self.__frame.reparent_to(self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = label.Label(text='Multiplayer Setup', align='center',
                          size=(0.8, 0.1), pos=(0, -0.4), font_size=0.06,
                          font=fnt, text_color=common.TITLE_TXT_COLOR, alpha=0)
        tit.reparent_to(self.__frame)
        tit.origin = Origin.CENTER
        self.__back: button.Button = None
        self.__drawpref: List[button.Button] = None
        self.__username: entry.Entry = None
        self.__password: entry.Entry = None
        self.__useraction: button.Button = None
        self.__dlg: Dialogue = None
        self.__update_data = {}
        self.__setup_menu_buttons()
        self.__root.hide()

    def enter_multiplayer_settings(self):
        """Enter state -> Setup."""
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        self.__back.pos = pos_x, -0.38
        if not self.mps.ctrl.noaccount:
            self.__useraction.change_text('Update')
        self.__update_drawpref()
        self.__root.show()

    def exit_multiplayer_settings(self):
        """Exit state -> Setup."""
        self.__root.hide()
        if self.__dlg is not None:
            self.__hide_dlg()

    def __update_drawpref(self, option: int = None):
        if option is not None:
            drawpref = option
        else:
            drawpref = self.mps.dbh.draw_count_preference
        for i in range(4):
            if drawpref == 4:
                self.__drawpref[i].enabled = False
                continue
            if i == drawpref:
                self.__drawpref[i].enabled = False
            else:
                self.__drawpref[i].enabled = True

    def __hide_dlg(self):
        self.__dlg.hide()
        self.__frame.show()

    def __gen_dlg(self, txt: str):
        if self.__dlg is None:
            fnt = self.config.get('font', 'bold')
            buttons = [DialogueButton(text='Ok',
                                      fmtkwargs=common.get_dialogue_btn_kw(),
                                      callback=self.__hide_dlg)]
            dlg = Dialogue(text=txt, buttons=buttons, margin=0.01,
                           size=(0.7, 0.7), font=fnt, align='center',
                           frame_color=common.FRAME_COLOR_STD,
                           border_thickness=0.01,
                           corner_radius=0.05, multi_sampling=2)
            dlg.pos = -0.35, -0.35
            dlg.reparent_to(self.ui.center)
            dlg.depth = 1000
            self.__dlg = dlg
        else:
            self.__dlg.text = txt
            self.__dlg.show()
        self.__frame.hide()

    def __setup_menu_buttons(self):
        kwargs = common.get_menu_sym_btn_kw()
        self.__back = button.Button(name='back button', pos=(0, -0.38),
                                    text=common.BACK_SYM, **kwargs)
        self.__back.origin = Origin.CENTER
        self.__back.reparent_to(self.__frame)
        self.__back.onclick(self.request, 'multiplayer_menu')

        lbl = label.Label(name='username label', text=chr(0xf007),
                          pos=(-0.42, -0.195), **kwargs)
        lbl.reparent_to(self.__frame)
        self.__username = entry.Entry(name='username entry', size=(0.7, 0.1),
                                      pos=(-0.29, -0.195), hint_text='Username',
                                      **common.get_entry_kw())
        self.__username.reparent_to(self.__frame)
        self.__username.onenter(self.__useractioncb)
        self.__username.text = self.config.get('mp', 'user', fallback='')

        lbl = label.Label(name='username label', text=chr(0xfcf3),
                          pos=(-0.42, -0.075), **kwargs)
        lbl.reparent_to(self.__frame)
        self.__password = entry.Entry(name='password entry', size=(0.7, 0.1),
                                      pos=(-0.29, -0.075), hint_text='Password',
                                      masked=chr(0xf444),
                                      **common.get_entry_kw())
        self.__password.reparent_to(self.__frame)
        self.__password.onenterfocus(self.__clearpw)
        self.__password.onenter(self.__useractioncb)
        if self.config.get('mp', 'password', fallback=''):
            self.__password.text = UNCHANGED

        kwargs['size'] = 0.8, 0.1
        kwargs['font_size'] = 0.045
        kwargs['corner_radius'] = 0.045
        lbl = label.Label(name='account label',
                          text='User account', pos=(0, -0.27),
                          **kwargs)
        lbl.origin = Origin.CENTER
        lbl.reparent_to(self.__frame)

        lbl = label.Label(name='draw count pref label',
                          text='Draw count preference', pos=(0, 0.22),
                          **kwargs)
        lbl.origin = Origin.CENTER
        lbl.reparent_to(self.__frame)

        kwargs = common \
            .get_settings_btn_kw(font_size=0.05,
                                 border_thickness=0.005,
                                 down_border_thickness=0.007,
                                 disabled_border_thickness=0.006,
                                 corner_radius=0.045)
        self.__useraction = button.Button(name='account action btn',
                                          size=(0.7, 0.1),
                                          text='Login / New Account',
                                          pos=(-0.29, 0.038), **kwargs)
        self.__useraction.reparent_to(self.__frame)
        self.__useraction.onclick(self.__useractioncb)

        # Draw Preference
        self.__drawpref = []
        kwargs['font_size'] = 0.0315
        btn = button.Button(name='both button', text='Both', size=(0.12, 0.1),
                            pos=(-0.425, 0.3), **kwargs)
        btn.reparent_to(self.__frame)
        btn.onclick(self.__set_drawpref, 0)
        self.__drawpref.append(btn)
        btn = button.Button(name='one button', text='One only',
                            size=(0.175, 0.1), pos=(-0.29, 0.3), **kwargs)
        btn.reparent_to(self.__frame)
        btn.onclick(self.__set_drawpref, 1)
        self.__drawpref.append(btn)
        btn = button.Button(name='three button', text='Three only',
                            size=(0.22, 0.1), pos=(-0.1, 0.3), **kwargs)
        btn.reparent_to(self.__frame)
        btn.onclick(self.__set_drawpref, 2)
        self.__drawpref.append(btn)
        btn = button.Button(name='no mp button', text='No Multiplayer',
                            size=(0.29, 0.1), pos=(0.135, 0.3), **kwargs)
        btn.reparent_to(self.__frame)
        btn.onclick(self.__set_drawpref, 3)
        self.__drawpref.append(btn)

    def __useractioncb(self) -> None:
        if self.mps.ctrl.noaccount:
            if not self.__username.text or not self.__password.text:
                self.__gen_dlg('CANNOT BE EMPTY\n\nPlease insert\n'
                               'a valid username\nand password\n\n\n')
                return
            if not 2 < len(self.__username.text) < 31:
                self.__gen_dlg('Username must\nbe between 3\n'
                               'and 30 characters\n\n\n')
                return
            req = self.mps.ctrl.create_new_account(self.__username.text.strip(),
                                                   self.__password.text)
            self.mps.ctrl.register_callback(req, self.__new_account)
            self.statuslbl.text = 'Attempting to connect...'
            self.statuslbl.show()
        else:
            if not self.__username.text or not self.__password.text:
                self.__gen_dlg('CANNOT BE EMPTY\n\nPlease insert\n'
                               'a valid username\nand password\n\n\n')
                return
            if not 2 < len(self.__username.text) < 31:
                self.__gen_dlg('Username must\nbe between 3\n'
                               'and 30 characters\n\n\n')
                return
            if self.__username.text == self.config.get('mp', 'user',
                                                       fallback='') \
                  and self.__password.text == UNCHANGED:
                return
            if self.mps.login != 0:
                req = self.mps.ctrl.update_user_ranking()
                self.mps.ctrl.register_callback(req, self.__update_acc)
            else:
                self.__update_acc()

    def __update_acc(self, rescode: int = None) -> None:
        if rescode is not None and rescode != 0:
            self.__gen_dlg(f'Unable to update\n\n'
                           f'{mpctrl.RESTXT[rescode]}\n\n')
            return

        self.__update_data['user'] = False
        self.__update_data['password'] = False
        self.__update_data['msg'] = ''
        if self.__username.text != self.config.get('mp', 'user', fallback=''):
            req = self.mps.ctrl.change_username(self.__username.text.strip())
            self.mps.ctrl.register_callback(req, self.__user_change)
            self.__update_data['user'] = True
        if self.__password.text != UNCHANGED:
            req = self.mps.ctrl.change_password(self.__password.text)
            self.mps.ctrl.register_callback(req, self.__passwd_change)
            self.__update_data['password'] = True
        if self.__update_data['user'] or self.__update_data['password']:
            self.statuslbl.text = 'Updating...'
            self.statuslbl.show()

    def __user_change(self, rescode: int) -> None:
        if rescode != 0 and self.__update_data['password']:
            self.__update_data['msg'] = 'Failed to change\nusername\n'
            self.__update_data['user'] = False
            self.__username.text = self.config.get('mp', 'user', fallback='')
            return
        if self.__update_data['password']:
            self.__update_data['user'] = False
            return
        msg = 'SUCCESS\n'
        if rescode != 0:
            msg = f'ERROR\n\nFailed to change\nusername\n' \
                  f'{self.__update_data["msg"]}'
        self.__gen_dlg(msg)
        self.__update_data['user'] = False
        self.__username.text = self.config.get('mp', 'user', fallback='')
        self.statuslbl.hide()

    def __passwd_change(self, rescode: int) -> None:
        if rescode != 0 and self.__update_data['user']:
            self.__update_data['msg'] = 'Failed to change\npassword\n'
            self.__update_data['password'] = False
            self.__password.text = UNCHANGED
            return
        if self.__update_data['user']:
            self.__update_data['password'] = False
            self.__password.text = UNCHANGED
            return
        msg = 'SUCCESS\n'
        if rescode != 0:
            msg = f'ERROR\n\nFailed to change\npassword\n' \
                  f'{self.__update_data["msg"]}'
        self.__gen_dlg(msg)
        self.__update_data['password'] = False
        self.__password.text = UNCHANGED
        self.statuslbl.hide()

    def __new_account(self, rescode: int) -> None:
        if rescode == 0:
            logger.info('New account created successfully.')
            self.statuslbl.hide()
            self.__gen_dlg('Success')
            self.__useraction.change_text('Update')
            self.__password.text = UNCHANGED
            self.__update_drawpref()
        else:
            logger.info(f'Unable to create account, got return code {rescode}')
            self.config.set('mp', 'user', self.__username.text)
            pwhash = util.generate_hash(self.__password.text)
            self.config.set('mp', 'password', util.encode_hash(pwhash))
            self.config.save()
            req = self.mps.ctrl.update_user_ranking()
            self.mps.ctrl.register_callback(req, self.__login_success)
            self.statuslbl.text = 'Attempting login...'

    def __login_success(self, rescode: int) -> None:
        self.statuslbl.hide()
        if rescode == 5:
            self.__gen_dlg('Unable to create\nor login to account!\n\n'
                           'Either wrong password\nor the username\n'
                           'is already taken\n\n')
        elif rescode == 0:
            self.__gen_dlg('Login successful\n')
            self.__update_drawpref()
            self.__useraction.change_text('Update')
            self.__password.text = UNCHANGED
            return
        else:
            self.__gen_dlg('LOGIN FAILED!\n\ncheck provided\n'
                           'username/password\n\n\n')
        self.config.set('mp', 'user', '')
        self.config.set('mp', 'password', '')
        self.config.save()

    def __set_drawpref(self, option: int) -> None:
        req = self.mps.ctrl.set_draw_count_pref(option)
        self.mps.ctrl.register_callback(req, self.__drawpref_set)
        self.statuslbl.text = 'Updating...'
        self.statuslbl.show()
        self.__update_drawpref(option)

    def __drawpref_set(self, rescode: int) -> None:
        self.statuslbl.hide()
        if rescode == 0:
            self.__update_drawpref()
        else:
            self.__gen_dlg(f'REQUEST FAILED:\n\n{mpctrl.RESTXT[rescode]}')

    def __clearpw(self):
        if self.__password.text == UNCHANGED:
            self.__password.text = ''
