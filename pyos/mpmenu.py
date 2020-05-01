"""
Provides the different menus in the app.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

from foolysh.scene.node import Origin
from foolysh.ui import button, frame, entry, label

import app
import buttonlist
import common
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
__version__ = '0.3'

NOACCTXT = """No online account
configured.
Go to settings """ + chr(0xf178) + ' ' + chr(0xf013) + """
in the multiplayer
menu and enter your
account info.


"""


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
                                   frame_color=(40, 120, 20),
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2)
        self.__frame.reparent_to(self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = label.Label(text='Multiplayer', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt,
                          text_color=(255, 255, 255, 255), alpha=0)
        tit.reparent_to(self.__frame)
        tit.origin = Origin.CENTER
        self.__buttons: MenuButtons = None
        self.__setup_menu_buttons()
        self.__dlg: Dialogue = None
        self.__root.hide()

    def enter_multiplayer_menu(self):
        """Enter state -> Setup."""
        if not self.mps.ctrl.active:
            self.mps.ctrl.start_service()
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        self.__buttons.settings.pos = pos_x, 0.38
        self.__buttons.back.pos = pos_x, -0.38
        if self.mps.ctrl.noaccount:
            if self.previous_state == 'main_menu':
                self.__gen_dlg(NOACCTXT)
            self.__buttons.challenges.enabled = False
            self.__buttons.friends.enabled = False
            self.__buttons.leaderboard.enabled = False
        else:
            self.__buttons.challenges.enabled = True
            self.__buttons.friends.enabled = True
            self.__buttons.leaderboard.enabled = True
        self.__root.show()

    def exit_multiplayer_menu(self):
        """Exit state -> Setup."""
        self.__root.hide()
        if self.__dlg is not None:
            self.__dlg.hide()

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
                           size=(0.7, 0.7), font=fnt, align='left',
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
                             text=chr(0xf80c), **kwargs)
        back.origin = Origin.CENTER
        back.reparent_to(self.__frame)
        back.onclick(self.request, 'main_menu')
        self.__buttons = MenuButtons(challenges, leaderboard, friends, settings,
                                     back)


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
                                 frame_color=(255, 255, 255),
                                 border_color=(0,) * 3, border_thickness=0.005,
                                 corner_radius=0.03, multi_sampling=2)


class Challenges(app.AppBase):
    """Challenges view."""
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__root = self.ui.center.attach_node('MP Challenges Root')
        self.__frame = frame.Frame('challenges background', size=(0.9, 0.9),
                                   frame_color=(142, 55, 22),
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2)
        self.__frame.reparent_to(self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = label.Label(text='Challenges', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt,
                          text_color=(255, 255, 255, 255), alpha=0)
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
        self.__data += [chr(i) * 32 for i in range(65, 101)]
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
                             text=chr(0xf80c), **kwargs)
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


class Friends(app.AppBase):
    """Friends view."""
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__root = self.ui.center.attach_node('MP Friends Root')
        self.__frame = frame.Frame('friends background', size=(0.9, 0.9),
                                   frame_color=(218, 165, 32),
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2)
        self.__frame.reparent_to(self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = label.Label(text='Friends', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt,
                          text_color=(255, 255, 255, 255), alpha=0)
        tit.reparent_to(self.__frame)
        tit.origin = Origin.CENTER
        self.__data: List[str] = []
        self.__btnlist: buttonlist.ButtonList = None
        self.__back: button.Button = None
        self.__new: button.Button = None
        self.__fltr: int = None
        self.__setup_menu_buttons()
        self.__root.hide()

    def enter_friends(self):
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

    def exit_friends(self):
        """Exit state -> Setup."""
        self.__root.hide()

    def __setup_menu_buttons(self):
        self.__btnlist = _gen_btnlist(self.config.get('font', 'normal'),
                                      self.config.get('font', 'bold'),
                                      self.__data, (self.__listclick,
                                                    self.__filter), 4,
                                      (0.85, 0.625), self.__frame,
                                      ['Friends', 'Pending', 'Blocked'])
        self.__data += [chr(i) * 32 for i in range(65, 101)]
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
        newb.onclick(self.__new_friend)
        back = button.Button(name='back button', pos=(pos_x, -0.38),
                             text=chr(0xf80c), **kwargs)
        back.origin = Origin.CENTER
        back.reparent_to(self.__frame)
        back.onclick(self.request, 'multiplayer_menu')
        self.__new = newb
        self.__back = back

    def __new_friend(self):
        # TODO: Open New Friend Dialogue
        self.__data.pop()
        self.__btnlist.update_content()

    def __filter(self, fltr: int = None) -> None:
        # TODO: Update the content of the data list
        pass

    def __listclick(self, pos: int) -> None:
        print(f'clicked on "{self.__data[pos]}"')
        # TODO: Open Challenge Dialogue


class Leaderboard(app.AppBase):
    """Leaderboard view."""
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__root = self.ui.center.attach_node('MP Leaderboard Root')
        self.__frame = frame.Frame('leaderboard background', size=(0.9, 0.9),
                                   frame_color=(105, 161, 0),
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2)
        self.__frame.reparent_to(self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = label.Label(text='Leaderboard', align='center', size=(0.8, 0.1),
                          pos=(0, -0.4), font_size=0.06, font=fnt,
                          text_color=(255, 255, 255, 255), alpha=0)
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
                                    text=chr(0xf80c), **kwargs)
        self.__back.origin = Origin.CENTER
        self.__back.reparent_to(self.__frame)
        self.__back.onclick(self.request, 'multiplayer_menu')

    def __listclick(self, entry: int) -> None:
        print(f'clicked on "{self.__data[entry]}"')
        # TODO: Open Challenge Dialogue


class MultiplayerSettings(app.AppBase):
    """MultiplayerSettings view."""
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__root = self.ui.center.attach_node('MP Settings Root')
        self.__frame = frame.Frame('mp settings background', size=(0.9, 0.9),
                                   frame_color=(60, ) * 3,
                                   border_thickness=0.01, corner_radius=0.05,
                                   multi_sampling=2)
        self.__frame.reparent_to(self.__root)
        self.__frame.origin = Origin.CENTER
        fnt = self.config.get('font', 'bold')
        tit = label.Label(text='Multiplayer Setup', align='center',
                          size=(0.8, 0.1), pos=(0, -0.4), font_size=0.06,
                          font=fnt, text_color=(255, 255, 255, 255), alpha=0)
        tit.reparent_to(self.__frame)
        tit.origin = Origin.CENTER
        self.__back: button.Button = None
        self.__setup_menu_buttons()
        self.__root.hide()

    def enter_multiplayer_settings(self):
        """Enter state -> Setup."""
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        # pylint: disable=no-member
        self.__back.pos = pos_x, -0.38
        # pylint: enable=no-member
        self.__root.show()

    def exit_multiplayer_settings(self):
        """Exit state -> Setup."""
        self.__root.hide()

    def __setup_menu_buttons(self):
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        kwargs = common.get_menu_sym_btn_kw()
        self.__back = button.Button(name='back button', pos=(pos_x, -0.38),
                                    text=chr(0xf80c), **kwargs)
        self.__back.origin = Origin.CENTER
        self.__back.reparent_to(self.__frame)
        self.__back.onclick(self.request, 'multiplayer_menu')

        lbl = label.Label(name='username label', text=chr(0xf007),
                          pos=(-0.42, -0.195), **kwargs)
        lbl.reparent_to(self.__frame)
        user = entry.Entry(name='username entry', size=(0.7, 0.1),
                           pos=(-0.29, -0.195), margin=0.01,
                           hint_text='Username',
                           hint_text_color=(10, 10, 10, 180),
                           font=self.config.get('font', 'bold'), font_size=0.05,
                           text_color=(10, 10, 10, 255),
                           align='left', frame_color=(255, 255, 255),
                           border_thickness=0.001, border_color=(0, 0, 0),
                           corner_radius=0.02, alpha=255)
        user.reparent_to(self.__frame)

        lbl = label.Label(name='username label', text=chr(0xfcf3),
                          pos=(-0.42, -0.075), **kwargs)
        lbl.reparent_to(self.__frame)
        password = entry.Entry(name='password entry', size=(0.7, 0.1),
                               pos=(-0.29, -0.075), margin=0.01,
                               hint_text='Password',
                               hint_text_color=(10, 10, 10, 180),
                               font=self.config.get('font', 'bold'),
                               font_size=0.05, text_color=(10, 10, 10, 255),
                               align='left', frame_color=(255, 255, 255),
                               border_thickness=0.001, border_color=(0, 0, 0),
                               corner_radius=0.02, alpha=255)
        password.reparent_to(self.__frame)

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
        buttons = []
        btn = button.Button(name='account action btn', size=(0.7, 0.1),
                            text='Login / New Account', pos=(-0.29, 0.038),
                            **kwargs)
        btn.reparent_to(self.__frame)
        kwargs['font_size'] = 0.0315
        btn = button.Button(name='both button', text='Both', size=(0.12, 0.1),
                            pos=(-0.425, 0.3), **kwargs)
        btn.reparent_to(self.__frame)
        buttons.append(btn)
        btn = button.Button(name='one button', text='One only',
                            size=(0.175, 0.1), pos=(-0.29, 0.3), **kwargs)
        btn.reparent_to(self.__frame)
        buttons.append(btn)
        btn = button.Button(name='three button', text='Three only',
                            size=(0.22, 0.1), pos=(-0.1, 0.3), **kwargs)
        btn.reparent_to(self.__frame)
        buttons.append(btn)
        btn = button.Button(name='no mp button', text='No Multiplayer',
                            size=(0.29, 0.1), pos=(0.135, 0.3), **kwargs)
        btn.reparent_to(self.__frame)
        buttons.append(btn)
