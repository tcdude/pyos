"""
Common constants and functions.
"""

from collections import OrderedDict
from dataclasses import dataclass
import datetime
from enum import Enum
from typing import Optional

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
__version__ = '0.2'

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
except ImportError:
    CACHEDIR = 'cache/'
    DATAFILE = 'gamedata.db'

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
    'font': OrderedDict([('normal', 'fonts/SpaceMono.ttf'),
                         ('bold', 'fonts/SpaceMonoBold.ttf')])
}
OVERWRITE_PYOS = ['card_ratio', 'padding', 'status_size', 'toolbar_size',
                  'click_threshold', 'auto_solve_delay',
                  'datafile', 'dailyseeds']
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
