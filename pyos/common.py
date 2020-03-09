"""
Common constants and functions.
"""

from dataclasses import dataclass
from enum import Enum
from logging.config import dictConfig
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

# Logging
def setup_dict_config(log_level: str) -> None:
    """Logging dictConfig."""
    dictConfig({
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'standard': {
                'format': '%(levelname)s %(filename)s:%(funcName)s:'
                          '%(lineno)d => %(message)s'
            },
        },
        'handlers': {
            'default': {
                'level': log_level,
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': log_level,
                'propagate': True
            }
        }
    })


# Timing
AUTO_SLOW = 0.5
AUTO_FAST = 0.3

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
