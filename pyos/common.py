"""
Common constants and functions.
"""

from collections import OrderedDict
from dataclasses import dataclass
import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

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

# Global Constants
COLORS = tuple('dchs')
DENOMINATIONS = tuple('a23456789') + ('10',) + tuple('jqk')

# Paths
BACKGROUND = 'images/bg.png'
CARDBACK = 'images/card_back.png'
BOTTOM_BAR_IMG = 'images/bt_bar.png'
FOUNDATION = 'images/f_empty.png'
STACK = 'images/s_empty.png'
TABLEAU = 'images/t_empty.png'
WASTE = 'images/w_empty.png'
try:
    import android  # pylint: disable=unused-import
    CACHEDIR = '../cache'
    DATAFILE = '../gamedata.db'
    MPDATAFILE = '../mp.db'
except ImportError:
    CACHEDIR = 'cache/'
    DATAFILE = 'gamedata.db'
    MPDATAFILE = 'mp.db'

# Config
DEFAULTCONFIG = {
    'base': OrderedDict([('window_title', 'Adfree Simple Solitaire'),
                         ('asset_pixel_ratio', '4712'),
                         ('window_size', '480x800'),
                         ('asset_dir', 'assets/'),
                         ('cache_dir', CACHEDIR),
                         ('drag_threshold', '0.025')]),
    'pyos': OrderedDict([('winner_deal', 'True'), ('draw_one', 'True'),
                         ('tap_move', 'True'), ('auto_foundation', 'False'),
                         ('waste_to_foundation', 'False'),
                         ('auto_solve', 'True'), ('auto_flip', 'True'),
                         ('left_handed', 'False'), ('state_file', 'state.bin'),
                         ('card_ratio', '1.3968253968253967'),
                         ('padding', '0.06'), ('status_size', '0.96, 0.08'),
                         ('toolbar_size', '0.96, 0.12'),
                         ('click_threshold', '0.06'), ('log_level', 'INFO'),
                         ('auto_solve_delay', '0.25'), ('orientation', 'auto'),
                         ('datafile', DATAFILE),
                         ('dailyseeds', 'assets/other/dailyseeds.bin')]),
    'mp': OrderedDict([('server', 'pyos.tizilogic.com'), ('port', '22864'),
                       ('user', ''), ('password', ''), ('bufsize', '4096'),
                       ('uds', './mp.sock'), ('datafile', 'mp.db')]),
    'font': OrderedDict([('normal', 'fonts/SpaceMono.ttf'),
                         ('bold', 'fonts/SpaceMonoBold.ttf')])
}
OVERWRITE_PYOS = ['card_ratio', 'padding', 'status_size', 'toolbar_size',
                  'click_threshold', 'auto_solve_delay',
                  'datafile', 'dailyseeds']
OVERWRITE_MP = ['server', 'port', 'bufsize', 'uds', 'datafile']
OVERWRITE_FONT = ['normal', 'bold']

# Daily deal
START_DATE = datetime.datetime(year=2020, month=3, day=13)


# Types

class TableArea(Enum):
    """Enumeration to describe different areas on the table."""
    STACK = 0
    WASTE = 1
    TABLEAU = 2
    FOUNDATION = 3
    NONE = 4


@dataclass
class TableLocation:
    """
    Typed class to specify an exact location and state of a card.

    Attributes:
        area: TableArea
        visible: visibility of the card
        pile_id: if the TableArea has multiple piles, index of the pile.
        card_id: the index of the card in the pile.
    """
    area: TableArea
    visible: Optional[bool] = True
    pile_id: Optional[int] = None
    card_id: Optional[int] = None


# Formatting

IN_SYM = chr(0xf234)
OUT_SYM = chr(0xf1d8)
ACC_SYM = chr(0xf00c)
DEN_SYM = chr(0xf00d)
BLK_SYM = chr(0xf05e)
BACK_SYM = chr(0xf80c)
NEW_SYM = chr(0xf893)
RES_SYM = chr(0xf021)
UNDO_SYM = chr(0xfa4b)
MENU_SYM = chr(0xf85b)

FRAME_COLOR_STD = 40, 120, 20
BTNLIST_FRAME_COLOR = 255, 255, 255
CHALLENGES_FRAME_COLOR = 142, 55, 22
FRIENDS_FRAME_COLOR = 218, 165, 32
LEADERBOARD_FRAME_COLOR = 105, 161, 0
SETTINGS_FRAME_COLOR = 60, 60, 60
TOOLBAR_FRAME_COLOR = 160, 160, 160

BTNLIST_BORDER_COLOR = 0, 0, 0
TOOLBAR_BORDER_COLOR = 255, 255, 255

TITLE_TXT_COLOR = 255, 255, 255, 255
STATUS_TXT_COLOR = 220, 220, 220, 240

MENU_TXT_BTN_KW = {'font': DEFAULTCONFIG['font']['bold'],
                   'text_color': (0, 50, 0, 255),
                   'frame_color': (200, 220, 200),
                   'down_text_color': (255, 255, 255, 255),
                   'border_thickness': 0.005, 'down_border_thickness': 0.008,
                   'border_color': (0, 50, 0),
                   'down_border_color': (255, 255, 255),
                   'disabled_border_color': (140, ) * 3,
                   'disabled_text_color': (140, ) * 3,
                   'corner_radius': 0.05, 'multi_sampling': 2,
                   'align': 'center'}
MENU_SYM_BTN_KW = {'font': DEFAULTCONFIG['font']['bold'],
                   'text_color': (255, ) * 4, 'font_size': 0.09,
                   'frame_color': (0, ) * 3, 'border_color': (255, ) * 3,
                   'down_text_color': (0, 0, 0, 255), 'alpha': 40,
                   'align': 'center', 'size': (0.11, 0.11),
                   'border_thickness': 0.003,
                   'down_border_thickness': 0.004,
                   'corner_radius': 0.05, 'multi_sampling': 2,}
SETTINGS_BTN_KW = {'font': DEFAULTCONFIG['font']['bold'],
                   'font_size': 0.0355, 'text_color': (0, 0, 0, 255),
                   'down_text_color': (255, 255, 255, 255),
                   'border_color': (0, 0, 0),
                   'down_border_color': (255, 255, 255),
                   'disabled_text_color': (255, 255, 255, 255),
                   'disabled_frame_color': (160, 160, 160),
                   'disabled_border_color': (255, 255, 255),
                   'multi_sampling': 2, 'align': 'center', 'margin': 0.01}
DAYDEAL_CELL_BTN_KW = {'font': DEFAULTCONFIG['font']['bold'],
                       'font_size': 0.045, 'text_color': (255, 255, 255, 225),
                       'down_text_color': (255, 255, 255, 255),
                       'border_thickness': 0.005, 'border_color': (0, 50, 0),
                       'corner_radius': 0.01, 'multi_sampling': 2,
                       'align': 'center', 'margin': 0.01}
DIALOGUE_BTN_KW = {'size': (0.35, 0.1), 'font': DEFAULTCONFIG['font']['bold'],
                   'text_color': (0, 50, 0, 255),
                   'down_text_color': (255, 255, 255, 255),
                   'border_thickness': 0.005, 'down_border_thickness': 0.008,
                   'border_color': (0, 50, 0),
                   'down_border_color': (255, 255, 255), 'corner_radius': 0.05,
                   'multi_sampling': 2, 'align': 'center'}
TOOLBAR_BTN_KW = {'text_color': (0, 0, 0, 255),
                  'down_text_color': (255, 255, 255, 255),
                  'frame_color': (180, 180, 180), 'border_color': (0, 0, 0),
                  'down_border_color': (255, 255, 255), 'multi_sampling': 2,
                  'align': 'center', 'alpha': 230}
ENTRY_KW = {'margin': 0.01, 'hint_text_color': (10, 10, 10, 180),
            'font': DEFAULTCONFIG['font']['bold'], 'font_size': 0.05,
            'text_color': (10, 10, 10, 255), 'align': 'left',
            'frame_color': (255, 255, 255), 'border_thickness': 0.001,
            'border_color': (0, 0, 0), 'corner_radius': 0.02, 'alpha': 255}
STATUS_TXT_KW = {'size': (0.9, 0.2), 'pos': (0, 0), 'font_size': 0.05,
                 'font': DEFAULTCONFIG['font']['bold'],
                 'text_color': STATUS_TXT_COLOR, 'border_thickness': 0.005,
                 'corner_radius': 0.05, 'frame_color': SETTINGS_FRAME_COLOR,
                 'border_color': (0, 0, 0), 'align': 'center',
                 'multisampling': 2, 'alpha': 220}


def get_menu_txt_btn_kw(size: Tuple[float, float], **kwargs) -> Dict[str, Any]:
    """Build a kwargs dict for textual menu buttons."""
    kwa = {}
    kwa.update(MENU_TXT_BTN_KW)
    kwa['size'] = size
    kwa.update(kwargs)
    return kwa


def get_menu_sym_btn_kw(**kwargs) -> Dict[str, Any]:
    """Returns a kwargs dict of the symbol menu buttons."""
    kwa = {}
    kwa.update(MENU_SYM_BTN_KW)
    kwa.update(kwargs)
    return kwa


def get_settings_btn_kw(**kwargs) -> Dict[str, Any]:
    """
    Returns a kwargs dict for the settings buttons, updated with the provided
    `kwargs`.
    """
    kwa = {}
    kwa.update(SETTINGS_BTN_KW)
    kwa.update(kwargs)
    return kwa


def get_daydeal_cell_btn_kw(**kwargs) -> Dict[str, Any]:
    """Returns a kwargs dict for the daydeal cell buttons."""
    kwa = {}
    kwa.update(DAYDEAL_CELL_BTN_KW)
    kwa.update(kwargs)
    return kwa


def get_dialogue_btn_kw(**kwargs) -> Dict[str, Any]:
    """Returns a kwargs dict for the dialogue buttons."""
    kwa = {}
    kwa.update(DIALOGUE_BTN_KW)
    kwa.update(kwargs)
    return kwa


def get_toolbar_btn_kw(**kwargs) -> Dict[str, Any]:
    """Returns a kwargs dict for the toolbar buttons."""
    kwa = {}
    kwa.update(TOOLBAR_BTN_KW)
    kwa.update(kwargs)
    return kwa


def get_entry_kw(**kwargs) -> Dict[str, Any]:
    """Returns a kwargs dict for the entry fields."""
    kwa = {}
    kwa.update(ENTRY_KW)
    kwa.update(kwargs)
    return kwa


def gen_btnlist(item_font: str, filter_font: str, data: List[str],
                cbs: Tuple[Callable, Callable], itpp: int,
                size: Tuple[float, float], parent: object = None,
                filters: List[str] = None):
    """Generate a ButtonList instance used in the multiplayer section."""
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
                                 frame_color=BTNLIST_FRAME_COLOR,
                                 border_color=BTNLIST_BORDER_COLOR,
                                 border_thickness=0.005, corner_radius=0.03,
                                 multi_sampling=2)
