"""
Provides the different menus in the app.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

from foolysh.scene.node import Origin
from foolysh.ui import button, frame, label

import app
import buttonlist

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
        self.__root.hide()

    def enter_multiplayer_menu(self):
        """Enter state -> Setup."""
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        self.__buttons.settings.pos = pos_x, 0.38
        self.__buttons.back.pos = pos_x, -0.38
        self.__root.show()

    def exit_multiplayer_menu(self):
        """Exit state -> Setup."""
        self.__root.hide()

    def __setup_menu_buttons(self):
        kwargs = {'font': self.config.get('font', 'bold'),
                  'text_color': (0, 50, 0, 255), 'frame_color': (200, 220, 200),
                  'down_text_color': (255, 255, 255, 255),
                  'border_thickness': 0.005, 'down_border_thickness': 0.008,
                  'border_color': (0, 50, 0),
                  'down_border_color': (255, 255, 255),
                  'corner_radius': 0.05, 'multi_sampling': 2,
                  'align': 'center', 'size': (0.8, 0.1)}
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
        kwargs.update({'text_color': (255, ) * 4, 'font_size': 0.09,
                       'frame_color': (0, ) * 3,
                       'border_color': (255, ) * 3,
                       'down_text_color': (0, 0, 0, 255), 'alpha': 40,
                       'align': 'center', 'size': (0.11, 0.11),
                       'border_thickness': 0.003,
                       'down_border_thickness': 0.004,})
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


@dataclass
class FilterButtons:
    """Holds filter buttons. Expects a Dict[str, button.Button]."""
    buttons: Dict[str, button.Button]

    def __post_init__(self):
        for k in self.buttons:
            setattr(self, k, self.buttons[k])


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
        self.__chbtns: FilterButtons = None
        self.__setup_menu_buttons()
        self.__root.hide()

    def enter_challenges(self):
        """Enter state -> Setup."""
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        # pylint: disable=no-member
        self.__chbtns.back.pos = pos_x, -0.38
        self.__chbtns.new.pos = pos_x, 0.38
        # pylint: enable=no-member
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
        kwargs = {'font': self.config.get('font', 'bold'),
                  'text_color': (255, ) * 4, 'font_size': 0.09,
                  'frame_color': (0, ) * 3, 'border_color': (255, ) * 3,
                  'down_text_color': (0, 0, 0, 255), 'alpha': 40,
                  'align': 'center', 'size': (0.11, 0.11),
                  'border_thickness': 0.003, 'corner_radius': 0.05,
                  'down_border_thickness': 0.004,}
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
        self.__chbtns = FilterButtons({'new': newb, 'back': back})

    def __new_challenge(self):
        # TODO: Open New Challenge Dialogue
        pass

    def __filter(self, fltr: int = None) -> None:
        # TODO: Update the content of the data list
        pass

    def __listclick(self, entry: int) -> None:
        print(f'clicked on "{self.__data[entry]}"')
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
        self.__chbtns: FilterButtons = None
        self.__fltr: int = None
        self.__setup_menu_buttons()
        self.__root.hide()

    def enter_friends(self):
        """Enter state -> Setup."""
        if self.config.getboolean('pyos', 'left_handed', fallback=False):
            pos_x = -0.38
        else:
            pos_x = 0.38
        # pylint: disable=no-member
        self.__chbtns.back.pos = pos_x, -0.38
        self.__chbtns.new.pos = pos_x, 0.38
        # pylint: enable=no-member
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
        kwargs = {'font': self.config.get('font', 'bold'),
                  'text_color': (255, ) * 4, 'font_size': 0.09,
                  'frame_color': (0, ) * 3, 'border_color': (255, ) * 3,
                  'down_text_color': (0, 0, 0, 255), 'alpha': 40,
                  'align': 'center', 'size': (0.11, 0.11),
                  'border_thickness': 0.003, 'corner_radius': 0.05,
                  'down_border_thickness': 0.004,}
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
        self.__chbtns = FilterButtons({'new': newb, 'back': back})

    def __new_friend(self):
        # TODO: Open New Friend Dialogue
        self.__data.pop()
        self.__btnlist.update_content()

    def __filter(self, fltr: int = None) -> None:
        # TODO: Update the content of the data list
        pass

    def __listclick(self, entry: int) -> None:
        print(f'clicked on "{self.__data[entry]}"')
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
        # pylint: disable=no-member
        self.__back.pos = pos_x, -0.38
        # pylint: enable=no-member
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
        kwargs = {'font': self.config.get('font', 'bold'),
                  'text_color': (255, ) * 4, 'font_size': 0.09,
                  'frame_color': (0, ) * 3, 'border_color': (255, ) * 3,
                  'down_text_color': (0, 0, 0, 255), 'alpha': 40,
                  'align': 'center', 'size': (0.11, 0.11),
                  'border_thickness': 0.003, 'corner_radius': 0.05,
                  'down_border_thickness': 0.004,}
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
        kwargs = {'font': self.config.get('font', 'bold'),
                  'text_color': (255, ) * 4, 'font_size': 0.09,
                  'frame_color': (0, ) * 3, 'border_color': (255, ) * 3,
                  'down_text_color': (0, 0, 0, 255), 'alpha': 40,
                  'align': 'center', 'size': (0.11, 0.11),
                  'border_thickness': 0.003, 'corner_radius': 0.05,
                  'down_border_thickness': 0.004,}
        self.__back = button.Button(name='back button', pos=(pos_x, -0.38),
                                    text=chr(0xf80c), **kwargs)
        self.__back.origin = Origin.CENTER
        self.__back.reparent_to(self.__frame)
        self.__back.onclick(self.request, 'multiplayer_menu')