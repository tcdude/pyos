"""
Provides the Multiplayer Challenge State.
"""
# pylint: disable=too-many-lines

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple

from foolysh.scene import node
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
    gametypeview: node.Node
    gametypetitle: label.Label

    challengetxt: node.TextNode = None
    gametypetxt: node.TextNode = None
    gametypedraw: button.Button = None
    gametypescore: List[button.Button] = None
    gametypestart: button.Button = None
    gametypereject: button.Button = None

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
    gtdraw: int = 0
    gtscore: int = 0
    pending: Dict[int, int] = field(default_factory=dict)


@dataclass
class ChallengesDlg:
    """Holds the different dialogue instances in the Challenges menu."""
    newchallenge: Dialogue = None
    error: Dialogue = None
    challenge: Dialogue = None

    @property
    def all(self) -> Tuple[Dialogue, ...]:
        """Helper property to get all members."""
        return self.newchallenge, self.error, self.challenge


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
        chtit = label.Label(text='', align='center', size=(0.8, 0.1),
                            pos=(0, -0.4), font_size=0.06, font=fnt,
                            text_color=common.TITLE_TXT_COLOR, alpha=0)
        chtit.reparent_to(challengeview)
        chtit.origin = Origin.CENTER
        challengeview.hide()

        gametypeview = _frame.attach_node('MP Challenges gametypeview')
        gttit = label.Label(text='', align='center', size=(0.8, 0.1),
                            pos=(0, -0.4), font_size=0.06, font=fnt,
                            text_color=common.TITLE_TXT_COLOR, alpha=0)
        gttit.reparent_to(gametypeview)
        gttit.origin = Origin.CENTER
        gametypeview.hide()

        self.__nodes = ChallengesNodes(root, _frame, listview, newview,
                                       challengeview, chtit, gametypeview,
                                       gttit)
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
        if 'result' in self.fsm_global_data and self.fsm_global_data['result']:
            self.__show_resultview()
        elif 'start_challenge' in self.fsm_global_data \
              and self.fsm_global_data['start_challenge']:
            self.__gen_dlg('new', f'Select the number\nof rounds to play\n'
                                  f'or {common.BACK_SYM} to go back.\n\n')
            self.__data.idmap[0] = self.fsm_global_data['start_challenge']
            self.__data.active = 0
        else:
            self.__nodes.btnlist.update_content()
            self.__filter(self.__data.fltr)
        self.__nodes.root.show()

    def exit_challenges(self):
        """Exit state -> Setup."""
        self.__nodes.root.hide()
        for i in self.__dlgs.all:
            if i is not None and not i.hidden:
                i.hide()
        if self.__dlgs.newchallenge is not None:
            self.__dlgs.newchallenge.hide()

    def __send_pending_results(self, callback: Callable) -> None:
        for challenge_id, roundno in self.mps.dbh.unsent_results:
            seed, draw, _ = self.mps.dbh.get_round_info(challenge_id, roundno)
            res = self.systems.stats.result(seed, draw, True,
                                            challenge=challenge_id)
            if res is None:
                logger.debug(f'No result found for {challenge_id} {roundno}')
                continue
            dur, mvs, pts, _ = res
            req = self.mps.ctrl \
                .submit_challenge_round_result(challenge_id, roundno,
                                               (dur, pts, mvs))
            self.mps.ctrl.register_callback(req, self.__empty_pending, req,
                                            callback)
            self.__data.pending[req] = challenge_id, roundno
        if 'result' in self.fsm_global_data \
              and self.fsm_global_data['result'] is not None \
              and self.fsm_global_data['result'][0] == -2.0:
            challenge_id = self.state.challenge
            roundno = self.mps.dbh.roundno(challenge_id)
            # Ensure the challenge result is stored in the DB on forfeit
            self.mps.dbh.update_challenge_round(challenge_id, roundno,
                                                resuser=(-2.0, 0, 0))
            req = self.mps.ctrl \
                .submit_challenge_round_result(challenge_id, roundno,
                                               (-2.0, 0, 0))
            self.mps.ctrl.register_callback(req, self.__empty_pending, req,
                                            callback)
            self.__data.pending[req] = challenge_id, roundno

    def __empty_pending(self, rescode: int, req: int, callback: Callable
                        ) -> None:
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
        else:
            logger.debug(f'Transmission of pending result for challenge '
                         f'{self.__data.pending[req]} complete')
        self.__data.pending.pop(req)
        if not self.__data.pending:
            req = self.mps.ctrl.sync_challenges()
            self.mps.ctrl.register_callback(req, callback)
            self.global_nodes.show_status('Updating Challenges...')

    def __update_list(self) -> None:
        self.global_nodes.show_status('Sending results...')
        self.__send_pending_results(self.__update_listcb)
        if not self.__data.pending:
            req = self.mps.ctrl.sync_challenges()
            self.mps.ctrl.register_callback(req, self.__update_listcb)
            self.global_nodes.show_status('Updating Challenges...')

    def __update_listcb(self, rescode: int) -> None:
        self.global_nodes.hide_status()
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
        self.__data.data.clear()
        self.__data.idmap.clear()
        if self.__data.fltr == 1:
            data = self.mps.dbh.chwaiting
        elif self.__data.fltr == 2:
            data = self.mps.dbh.chfinished
        else:
            data = self.mps.dbh.chmyturn
        for i, (challenge_id, txt) in enumerate(data):
            self.__data.data.append(txt)
            self.__data.idmap[i] = challenge_id
        self.__nodes.btnlist.update_content()
        self.__update_filter()

    def __gen_dlg(self, dlg: str, txt: str) -> None:
        self.__hide_all_dlg()
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
        elif dlg == 'error':
            if self.__dlgs.error is None:
                fnt = self.config.get('font', 'bold')
                bkwa = common.get_dialogue_btn_kw(size=(0.25, 0.11))
                buttons = [DialogueButton(text='Back', fmtkwargs=bkwa,
                                          callback=self.__back)]
                dlg = Dialogue(text=txt, buttons=buttons, margin=0.01,
                               size=(0.7, 0.7), font=fnt, align='center',
                               frame_color=common.CHALLENGES_FRAME_COLOR,
                               border_thickness=0.01,
                               corner_radius=0.05, multi_sampling=2)
                dlg.pos = -0.35, -0.35
                dlg.reparent_to(self.ui.center)
                dlg.depth = 1000
                self.__dlgs.error = dlg
            else:
                self.__dlgs.error.text = txt
                self.__dlgs.error.show()
        elif dlg == 'challenge':
            if self.__dlgs.challenge is None:
                fnt = self.config.get('font', 'bold')
                bkwa = common.get_dialogue_btn_kw(size=(0.25, 0.11))
                buttons = [DialogueButton(text='Play', fmtkwargs=bkwa,
                                          callback=self.__start_round),
                           DialogueButton(text='Next', fmtkwargs=bkwa,
                                          callback=self.__next_round),
                           DialogueButton(text='Again', fmtkwargs=bkwa,
                                          callback=self.__show_newdlg),
                           DialogueButton(text='Back', fmtkwargs=bkwa,
                                          callback=self.__back)]
                dlg = Dialogue(text=txt, buttons=buttons, margin=0.01,
                               size=(0.7, 0.9), font=fnt, align='center',
                               frame_color=common.CHALLENGES_FRAME_COLOR,
                               border_thickness=0.01, font_size=0.035,
                               corner_radius=0.05, multi_sampling=2)
                dlg.pos = -0.35, -0.45
                dlg.reparent_to(self.ui.center)
                dlg.depth = 1000
                self.__dlgs.challenge = dlg
            else:
                self.__dlgs.challenge.text = txt
                self.__dlgs.challenge.show()

    def __hide_all_dlg(self) -> None:
        for dlg in self.__dlgs.all:
            if dlg is None:
                continue
            dlg.hide()

    def __challenge_req(self, rounds: int) -> None:
        fromnew = not self.__nodes.newview.hidden
        self.__dlgs.newchallenge.hide()
        userid = self.__data.idmap[self.__data.active]
        req = self.mps.ctrl.start_challenge(userid, rounds)
        self.mps.ctrl.register_callback(req, self.__challenge_reqcb, fromnew)
        self.global_nodes.show_status('Sending request...')

    def __challenge_reqcb(self, rescode: int, fromnew: bool) -> None:
        self.fsm_global_data['start_challenge'] = 0
        self.global_nodes.hide_status()
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
        if fromnew:
            self.__update_new_list()
        else:
            self.__show_listview()

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

        self.__setup_newview()
        self.__setup_gametypeview()

    def __setup_newview(self):
        # newview
        self.__nodes.newviewbtnlist = common \
            .gen_btnlist(self.config.get('font', 'normal'),
                         self.config.get('font', 'bold'), self.__data.data,
                         (self.__listclick, None), 8, (0.85, 0.7),
                         self.__nodes.newview)
        self.__nodes.newviewbtnlist.pos = 0, 0.06

    def __setup_gametypeview(self):
        # gametypeview
        self.__nodes.gametypetxt = self.__nodes.gametypeview \
            .attach_text_node(text='Choose the game type\nfor the round:\n\n',
                              text_color=common.TITLE_TXT_COLOR, align='center',
                              font=self.config.get('font', 'bold'),
                              font_size=0.05, multiline=True)
        self.__nodes.gametypetxt.origin = Origin.CENTER
        self.__nodes.gametypetxt.pos = 0, -0.2

        lbl = self.__nodes.gametypeview \
            .attach_text_node(text='Draw count:',
                              text_color=common.TITLE_TXT_COLOR,
                              font=self.config.get('font', 'bold'),
                              font_size=0.05)
        lbl.pos = 0, -0.1
        lbl.origin = Origin.CENTER

        self.__nodes.gametypedraw = button \
            .Button(text='One', pos=(-0.125, -0.05),
                    **common.get_dialogue_btn_kw(size=(0.25, 0.1)))
        self.__nodes.gametypedraw.reparent_to(self.__nodes.gametypeview)
        self.__nodes.gametypedraw.onclick(self.__toggle_gt, 'draw')

        lbl = self.__nodes.gametypeview \
            .attach_text_node(text='Score type:',
                              text_color=common.TITLE_TXT_COLOR,
                              font=self.config.get('font', 'bold'),
                              font_size=0.05)
        lbl.pos = 0, 0.125
        lbl.origin = Origin.CENTER
        self.__nodes.gametypescore = []
        btn = button \
            .Button(text='Fastest', pos=(-0.4, 0.175),
                    **common.get_dialogue_btn_kw(size=(0.25, 0.1)))
        btn.reparent_to(self.__nodes.gametypeview)
        btn.onclick(self.__toggle_gt, 'score', 0)
        self.__nodes.gametypescore.append(btn)
        btn = button \
            .Button(text='Moves', pos=(-0.125, 0.175),
                    **common.get_dialogue_btn_kw(size=(0.25, 0.1)))
        btn.reparent_to(self.__nodes.gametypeview)
        btn.onclick(self.__toggle_gt, 'score', 1)
        self.__nodes.gametypescore.append(btn)
        btn = button \
            .Button(text='Points', pos=(0.15, 0.175),
                    **common.get_dialogue_btn_kw(size=(0.25, 0.1)))
        btn.reparent_to(self.__nodes.gametypeview)
        btn.onclick(self.__toggle_gt, 'score', 2)
        self.__nodes.gametypescore.append(btn)

        self.__nodes.gametypestart = button \
            .Button(text='Start', pos=(-0.255, 0.3),
                    **common.get_dialogue_btn_kw(size=(0.25, 0.1)))
        self.__nodes.gametypestart.reparent_to(self.__nodes.gametypeview)
        self.__nodes.gametypestart.onclick(self.__newround)

        self.__nodes.gametypereject = button \
            .Button(text='Reject', pos=(0.005, 0.3),
                    **common.get_dialogue_btn_kw(size=(0.25, 0.1)))
        self.__nodes.gametypereject.reparent_to(self.__nodes.gametypeview)
        self.__nodes.gametypereject.onclick(self.__reject_challenge)

    def __back(self):
        for i in self.__dlgs.all:
            if i is not None and not i.hidden:
                i.hide()
                self.__show_listview()
                return
        if 'start_challenge' in self.fsm_global_data \
              and self.fsm_global_data['start_challenge']:
            self.fsm_global_data['start_challenge'] = 0
            self.request('friends')
            return
        if self.__nodes.listview.hidden:
            self.__show_listview()
            return
        self.request('multiplayer_menu')

    def __show_listview(self) -> None:
        if 'result' not in self.fsm_global_data \
              or self.fsm_global_data['result'] is None:
            self.state.challenge = -1
        self.__nodes.newview.hide()
        self.__nodes.challengeview.hide()
        self.__nodes.gametypeview.hide()
        self.__nodes.listview.show()
        self.__update_list()

    def __show_gametypeview(self) -> None:
        req = self.mps.ctrl \
            .update_other_user(self.mps.dbh.opponent_id(
                self.__data.idmap[self.__data.active]))
        self.mps.ctrl.register_callback(req, self.__show_gametypeviewcb)
        self.global_nodes.show_status('Updating preferences...')

    def __show_gametypeviewcb(self, rescode: int) -> None:
        self.global_nodes.hide_status()
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
            return
        self.__hide_all_dlg()
        self.__nodes.newview.hide()
        self.__nodes.challengeview.hide()
        self.__nodes.listview.hide()
        self.__nodes.gametypeview.show()
        dcp = self.mps.dbh.available_draw(self.__data.idmap[self.__data.active])
        if len(dcp) == 2 or 1 in dcp:
            self.__data.gtdraw = 0
            self.__nodes.gametypedraw.change_text('One')
        else:
            self.__data.gtdraw = 1
            self.__nodes.gametypedraw.change_text('Three')
        if len(dcp) == 1:
            self.__nodes.gametypedraw.enabled = False
        else:
            self.__nodes.gametypedraw.enabled = True
        self.__data.gtscore = 0
        for i, btn in enumerate(self.__nodes.gametypescore):
            if i:
                btn.enabled = True
            else:
                btn.enabled = False
        roundno = self.mps.dbh.roundno(self.__data.idmap[self.__data.active])
        if roundno < 0:
            logger.error('Challenge does not exist')
        elif roundno > 0:
            self.__nodes.gametypereject.hide()
            self.__nodes.gametypestart.x = -0.125
        else:
            self.__nodes.gametypereject.show()
            self.__nodes.gametypestart.x = -0.255
        self.__nodes.gametypetxt.text = f'Choose the game type\n' \
                                        f'for round {roundno + 1}:\n\n'
        oid = self.mps.dbh.opponent_id(self.__data.idmap[self.__data.active])
        other = self.mps.dbh.get_username(oid)
        rounds = self.mps.dbh.num_rounds(self.__data.idmap[self.__data.active])
        self.__nodes.gametypetitle.text = f'{other} ({roundno + 1}/{rounds})'

    def __show_resultview(self) -> None:
        self.__send_pending_results(self.__show_resultviewcb)
        if self.__data.pending:
            self.global_nodes.show_status('Sending Result...')

    def __show_resultviewcb(self, rescode: int, *unused_a, **unused_kw) -> None:
        self.global_nodes.hide_status()
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')

        self.__nodes.newview.hide()
        self.__nodes.challengeview.hide()
        self.__nodes.gametypeview.hide()
        otherid = self.mps.dbh.opponent_id(self.state.challenge)
        if self.mps.dbh.newround(self.state.challenge):
            self.__show_challengedlg(1)
        elif self.mps.dbh.challenge_complete(self.state.challenge):
            self.__show_challengedlg(2)
            self.__data.idmap.clear()
            self.__data.idmap[0] = otherid
            self.__data.active = 0
        else:
            self.__show_challengedlg()
        self.fsm_global_data['result'] = None
        self.state.need_new_game = True

    def __toggle_gt(self, event: str, value: int = None) -> None:
        if event == 'draw':
            if self.__data.gtdraw == 0:
                self.__nodes.gametypedraw.change_text('Three')
                self.__data.gtdraw = 1
            else:
                self.__nodes.gametypedraw.change_text('One')
                self.__data.gtdraw = 0
        elif event == 'score':
            self.__data.gtscore = value
            for i, btn in enumerate(self.__nodes.gametypescore):
                if i == value:
                    btn.enabled = False
                else:
                    btn.enabled = True

    def __newround(self) -> None:
        roundno = self.mps.dbh.roundno(self.__data.idmap[self.__data.active])
        newround = self.mps.dbh.newround(self.__data.idmap[self.__data.active])
        if roundno >= 0 and newround:
            req = self.mps.ctrl \
                .accept_challenge(self.__data.idmap[self.__data.active],
                                  3 if self.__data.gtdraw else 1,
                                  self.__data.gtscore)
        else:
            return
        self.mps.ctrl.register_callback(req, self.__newroundcb)
        self.global_nodes.show_status('Starting...')

    def __newroundcb(self, rescode: int) -> None:
        self.global_nodes.hide_status()
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
            self.__nodes.gametypeview.hide()
            self.__gen_dlg('error', f'Unable to start\nnew round\n\n'
                                    f'Error:\n"{mpctrl.RESTXT[rescode]}"\n')
            return
        self.__show_listview()
        self.state.challenge = self.__data.idmap[self.__data.active]
        self.__data.active = None
        self.request('game')

    def __reject_challenge(self) -> None:
        req = self.mps.ctrl \
            .reject_challenge(self.__data.idmap[self.__data.active])
        self.mps.ctrl.register_callback(req, self.__reject_challengecb)
        self.global_nodes.show_status('Rejecting...')

    def __reject_challengecb(self, rescode: int) -> None:
        self.global_nodes.hide_status()
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
        self.__data.active = None
        self.__show_listview()

    def __next_round(self) -> None:
        if self.state.challenge < 0:
            self.__gen_dlg('error', f'Error, !\n')
            return
        self.__data.idmap[0] = self.state.challenge
        self.__data.active = 0
        self.state.challenge = -1
        self.__show_gametypeview()

    def __new_challenge(self):
        self.__nodes.listview.hide()
        self.__nodes.newview.show()
        self.__update_new_list()

    def __show_newdlg(self):
        self.__gen_dlg('new', f'Select the number\nof rounds to play\n'
                              f'or {common.BACK_SYM} to go back.\n\n')

    def __show_challengedlg(self, action: int = None):
        if self.state.challenge is not None and self.state.challenge > -1:
            chid = self.state.challenge
        else:
            chid = self.__data.idmap[self.__data.active]
        self.__gen_dlg('challenge', self.mps.dbh.challenge_view(chid))
        for i in range(3):
            if i == action:
                self.__dlgs.challenge.toggle_button(i, True, True)
            else:
                self.__dlgs.challenge.toggle_button(i, False, False)

    def __update_new_list(self) -> None:
        req = self.mps.ctrl.sync_relationships()
        self.mps.ctrl.register_callback(req, self.__update_new_listcb)
        self.global_nodes.show_status('Updating Friends...')

    def __update_new_listcb(self, rescode: int) -> None:
        self.global_nodes.hide_status()
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
        data = self.mps.dbh.challenge_available
        self.__data.data.clear()
        self.__data.idmap.clear()
        for i, (user_id, username) in enumerate(data):
            self.__data.data.append(username)
            self.__data.idmap[i] = user_id
        self.__nodes.newviewbtnlist.update_content(True)

    def __start_round(self) -> None:
        self.__dlgs.challenge.hide()
        self.state.challenge = self.__data.idmap[self.__data.active]
        self.fsm_global_data['result'] = None
        self.__data.active = None
        self.request('game')

    def __filter(self, fltr: int = None) -> None:
        self.__data.fltr = fltr or 0
        self.__update_list()

    def __update_filter(self) -> None:
        cha = self.mps.dbh.challenge_actions
        myt = len(self.mps.dbh.chmyturn)
        if myt:
            sym = common.bubble_number(myt)
            self.__nodes.btnlist.update_filter(0, f'{sym} My Turn')
        else:
            self.__nodes.btnlist.update_filter(0, f'My Turn')
        if cha - myt:
            sym = common.bubble_number(cha - myt)
            self.__nodes.btnlist.update_filter(2, f'{sym} Finished')
        else:
            self.__nodes.btnlist.update_filter(2, f'Finished')

    def __listclick(self, pos: int) -> None:
        self.__data.active = pos
        if not self.__nodes.listview.hidden:
            if self.__data.fltr == 0:
                if self.mps.dbh.newround(self.__data.idmap[self.__data.active]):
                    self.__show_gametypeview()
                else:
                    self.__show_challengedlg(0)
            else:
                self.__show_challengedlg()
            return
        if not self.__nodes.newview.hidden:
            self.__show_newdlg()
            return
