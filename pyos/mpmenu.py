"""
Provides the different menus in the app.
"""

from dataclasses import dataclass
from typing import List

from foolysh.scene.node import Origin
from foolysh.ui import button, frame, entry, label
from loguru import logger

import app
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
        self.__pending_sync: int = 0
        self.__setup_menu_buttons()
        self.__dlg: Dialogue = None
        self.__root.hide()

    def enter_multiplayer_menu(self):
        """Enter state -> Setup."""
        logger.debug('Enter Multiplayer Menu')
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
        req = self.mps.ctrl.sync_challenges()
        self.mps.ctrl.register_callback(req, self.__update_notificationscb)
        req = self.mps.ctrl.sync_relationships()
        self.mps.ctrl.register_callback(req, self.__update_notificationscb)
        self.__pending_sync = 2
        self.global_nodes.show_status('Updating notifications...')

    def __update_notificationscb(self, rescode: int) -> None:
        self.global_nodes.hide_status()
        if rescode:
            logger.warning(f'Request failed: {mpctrl.RESTXT[rescode]}')
        self.__pending_sync -= 1
        if self.__pending_sync:
            return
        for but, num, txt, sym in zip((self.__buttons.challenges,
                                       self.__buttons.friends),
                                      (self.mps.dbh.challenge_actions,
                                       self.mps.dbh.friend_actions),
                                      ('  Challenges  ',
                                       ' ' * 3 + 'Friends' + ' ' * 3),
                                      (chr(0xf9e4), chr(0xf0c0))):
            txt = sym + txt
            txt += common.bubble_number(num) if num else sym
            but.change_text(txt)
            if num:
                but.labels[0].text_color = common.NTFY_MENU_TXT_COLOR
            else:
                but.labels[0].text_color = common.STD_MENU_TXT_COLOR

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


@dataclass
class MPSettingsNodes:
    """Holds the different Nodes for the MultiplayerSettings state."""
    back: button.Button = None
    drawpref: List[button.Button] = None
    username: entry.Entry = None
    password: entry.Entry = None
    useraction: button.Button = None


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
        self.__nodes: MPSettingsNodes = MPSettingsNodes()
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
        self.__nodes.back.pos = pos_x, -0.38
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
                self.__nodes.drawpref[i].enabled = False
                continue
            if i == drawpref:
                self.__nodes.drawpref[i].enabled = False
            else:
                self.__nodes.drawpref[i].enabled = True

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
        self.__nodes.back = button.Button(name='back button', pos=(0, -0.38),
                                          text=common.BACK_SYM, **kwargs)
        self.__nodes.back.origin = Origin.CENTER
        self.__nodes.back.reparent_to(self.__frame)
        self.__nodes.back.onclick(self.request, 'multiplayer_menu')

        lbl = label.Label(name='username label', text=chr(0xf007),
                          pos=(-0.42, -0.195), **kwargs)
        lbl.reparent_to(self.__frame)
        self.__nodes.username = entry.Entry(name='username entry',
                                            size=(0.7, 0.1),
                                            pos=(-0.29, -0.195),
                                            hint_text='Username',
                                            **common.get_entry_kw())
        self.__nodes.username.reparent_to(self.__frame)
        self.__nodes.username.onenter(self.__useractioncb)
        self.__nodes.username.text = self.config.get('mp', 'user', fallback='')

        lbl = label.Label(name='username label', text=chr(0xfcf3),
                          pos=(-0.42, -0.075), **kwargs)
        lbl.reparent_to(self.__frame)
        self.__nodes.password = entry.Entry(name='password entry',
                                            size=(0.7, 0.1),
                                            pos=(-0.29, -0.075),
                                            hint_text='Password',
                                            masked=chr(0xf444),
                                            **common.get_entry_kw())
        self.__nodes.password.reparent_to(self.__frame)
        self.__nodes.password.onenterfocus(self.__clearpw)
        self.__nodes.password.onenter(self.__useractioncb)
        if self.config.get('mp', 'password', fallback=''):
            self.__nodes.password.text = UNCHANGED

        kwargs['size'] = 0.8, 0.1
        kwargs['font_size'] = kwargs['corner_radius'] = 0.045
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
        self.__nodes.drawpref = []
        kwargs['font_size'] = 0.0315
        btn = button.Button(name='both button', text='Both', size=(0.12, 0.1),
                            pos=(-0.425, 0.3), **kwargs)
        btn.reparent_to(self.__frame)
        btn.onclick(self.__set_drawpref, 0)
        self.__nodes.drawpref.append(btn)
        btn = button.Button(name='one button', text='One only',
                            size=(0.175, 0.1), pos=(-0.29, 0.3), **kwargs)
        btn.reparent_to(self.__frame)
        btn.onclick(self.__set_drawpref, 1)
        self.__nodes.drawpref.append(btn)
        btn = button.Button(name='three button', text='Three only',
                            size=(0.22, 0.1), pos=(-0.1, 0.3), **kwargs)
        btn.reparent_to(self.__frame)
        btn.onclick(self.__set_drawpref, 2)
        self.__nodes.drawpref.append(btn)
        btn = button.Button(name='no mp button', text='No Multiplayer',
                            size=(0.29, 0.1), pos=(0.135, 0.3), **kwargs)
        btn.reparent_to(self.__frame)
        btn.onclick(self.__set_drawpref, 3)
        self.__nodes.drawpref.append(btn)

    def __useractioncb(self) -> None:
        if self.mps.ctrl.noaccount:
            if not self.__nodes.username.text or not self.__nodes.password.text:
                self.__gen_dlg('CANNOT BE EMPTY\n\nPlease insert\n'
                               'a valid username\nand password\n\n\n')
                return
            if not 2 < len(self.__nodes.username.text) < 14:
                self.__gen_dlg('Username must\nbe between 3\n'
                               'and 13 characters\n\n\n')
                return
            req = self.mps.ctrl \
                .create_new_account(self.__nodes.username.text.strip(),
                                    self.__nodes.password.text)
            self.mps.ctrl.register_callback(req, self.__new_account)
            self.global_nodes.show_status('Attempting to connect...')
        else:
            if not self.__nodes.username.text or not self.__nodes.password.text:
                self.__gen_dlg('CANNOT BE EMPTY\n\nPlease insert\n'
                               'a valid username\nand password\n\n\n')
                return
            if not 2 < len(self.__nodes.username.text) < 14:
                self.__gen_dlg('Username must\nbe between 3\n'
                               'and 13 characters\n\n\n')
                return
            if self.__nodes.username.text == self.config.get('mp', 'user',
                                                             fallback='') \
                  and self.__nodes.password.text == UNCHANGED:
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
        if self.__nodes.username.text != self.config \
              .get('mp', 'user', fallback=''):
            req = self.mps.ctrl \
                .change_username(self.__nodes.username.text.strip())
            self.mps.ctrl.register_callback(req, self.__user_change)
            self.__update_data['user'] = True
        if self.__nodes.password.text != UNCHANGED:
            req = self.mps.ctrl.change_password(self.__nodes.password.text)
            self.mps.ctrl.register_callback(req, self.__passwd_change)
            self.__update_data['password'] = True
        if self.__update_data['user'] or self.__update_data['password']:
            self.global_nodes.show_status('Updating...')

    def __user_change(self, rescode: int) -> None:
        if rescode != 0 and self.__update_data['password']:
            self.__update_data['msg'] = 'Failed to change\nusername\n'
            self.__update_data['user'] = False
            self.__nodes.username.text = self.config.get('mp', 'user',
                                                         fallback='')
            return
        if self.__update_data['password']:
            self.__update_data['user'] = False
            return
        msg = 'SUCCESS\n'
        if rescode != 0:
            msg = f'ERROR\n\nFailed to change\nusername\n' \
                  f'{self.__update_data["msg"]}'
        username = self.config.get('mp', 'user', fallback='')
        self.global_nodes.set_mpstatus(f'Logged in as {username}')
        self.__gen_dlg(msg)
        self.__update_data['user'] = False
        self.__nodes.username.text = self.config.get('mp', 'user', fallback='')
        self.global_nodes.hide_status()

    def __passwd_change(self, rescode: int) -> None:
        if rescode != 0 and self.__update_data['user']:
            self.__update_data['msg'] = 'Failed to change\npassword\n'
            self.__update_data['password'] = False
            self.__nodes.password.text = UNCHANGED
            return
        if self.__update_data['user']:
            self.__update_data['password'] = False
            self.__nodes.password.text = UNCHANGED
            return
        msg = 'SUCCESS\n'
        if rescode != 0:
            msg = f'ERROR\n\nFailed to change\npassword\n' \
                  f'{self.__update_data["msg"]}'
        username = self.config.get('mp', 'user', fallback='')
        self.global_nodes.set_mpstatus(f'Logged in as {username}')
        self.__gen_dlg(msg)
        self.__update_data['password'] = False
        self.__nodes.password.text = UNCHANGED
        self.global_nodes.hide_status()

    def __new_account(self, rescode: int) -> None:
        self.mps.login = rescode
        if rescode == 0:
            logger.info('New account created successfully.')
            self.global_nodes.hide_status()
            self.__gen_dlg('Success')
            self.__useraction.change_text('Update')
            self.__nodes.password.text = UNCHANGED
            self.__update_drawpref(0)
            self.mps.dbh.update_timestamp(0)
            username = self.config.get('mp', 'user', fallback='')
            self.global_nodes.set_mpstatus(f'Logged in as {username}')
        else:
            logger.info(f'Unable to create account, got return code {rescode}')
            self.config.set('mp', 'user', self.__nodes.username.text)
            pwhash = util.generate_hash(self.__nodes.password.text)
            self.config.set('mp', 'password', util.encode_hash(pwhash))
            self.config.save()
            req = self.mps.ctrl.update_user_ranking()
            self.mps.ctrl.register_callback(req, self.__login_success)
            self.global_nodes.show_status('Attempting login...')

    def __login_success(self, rescode: int) -> None:
        self.global_nodes.hide_status()
        self.mps.login = rescode
        if rescode == 5:
            self.__gen_dlg('Unable to create\nor login to account!\n\n'
                           'Either wrong password\nor the username\n'
                           'is already taken\n\n')
        elif rescode == 0:
            self.__gen_dlg('Login successful\n')
            self.__update_drawpref()
            self.__useraction.change_text('Update')
            self.__nodes.password.text = UNCHANGED
            self.mps.dbh.update_timestamp(0)
            username = self.config.get('mp', 'user', fallback='')
            self.global_nodes.set_mpstatus(f'Logged in as {username}')
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
        self.global_nodes.show_status('Updating...')
        self.__update_drawpref(option)

    def __drawpref_set(self, rescode: int) -> None:
        self.global_nodes.hide_status()
        if rescode == 0:
            self.__update_drawpref()
        else:
            self.__gen_dlg(f'REQUEST FAILED:\n\n{mpctrl.RESTXT[rescode]}')

    def __clearpw(self):
        if self.__nodes.password.text == UNCHANGED:
            self.__nodes.password.text = ''
