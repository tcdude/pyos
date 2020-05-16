"""
Provide the HUD class.
"""

from typing import Tuple
from typing import Type

from foolysh.scene import node

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


class HUD:
    """Class for holding the HUD."""

    def __init__(
            self,
            parent: Type[node.Node],
            size: Tuple[float, float],
            title_font: str,
            value_font: str
        ) -> None:
        self._size = size
        tmp_parent = parent.attach_node('HUD Holder')
        tmp_parent.depth = 500
        self._points_title = tmp_parent.attach_text_node(
            'Points Title',
            'Points:',
            title_font,
            size[1] * 0.45
        )
        self._points_value = tmp_parent.attach_text_node(
            'Points Value',
            '0',
            value_font,
            size[1] * 0.45
        )
        self._points_value.pos = 0, size[1] * 0.51
        self._time_title = tmp_parent.attach_text_node(
            'Time Title',
            'Time:',
            title_font,
            size[1] * 0.45
        )
        self._time_title.pos = size[0] * 0.5, 0
        self._time_value = tmp_parent.attach_text_node(
            'Time Value',
            '0:00',
            value_font,
            size[1] * 0.45
        )
        self._time_value.pos = size[0] * 0.4, size[1] * 0.51
        self._moves_title = tmp_parent.attach_text_node(
            'Moves Title',
            'Moves:',
            title_font,
            size[1] * 0.45
        )
        self._moves_title.pos = size[0] - 0.2, 0
        self._moves_value = tmp_parent.attach_text_node(
            'Moves Value',
            '0',
            value_font,
            size[1] * 0.45
        )
        self._moves_value.pos = size[0] - 0.2, size[1] * 0.51
        self._gametype = None

    def set_gametype(self, gametype: int = None) -> None:
        """Set the game type to display."""
        self._gametype = gametype
        if gametype is None:
            self._points_title.show()
            self._time_title.show()
            self._moves_title.show()
            self._points_value.show()
            self._time_value.show()
            self._moves_value.show()
            self._points_title.text = 'Points:'
            self._time_title.text = 'Time:'
            self._moves_title.text = 'Moves:'
        else:
            self._points_title.hide()
            self._moves_title.hide()
            self._points_value.hide()
            self._moves_value.hide()
            self._time_title.show()
            self._time_value.show()

        if gametype == 0:
            self._time_title.text = chr(0xf9e4) + ' Time: ' + chr(0xf9e4)
        elif gametype == 1:
            self._time_title.text = chr(0xf9e4) + ' Moves: ' + chr(0xf9e4)
        elif gametype == 2:
            self._time_title.text = chr(0xf9e4) + ' Points: ' + chr(0xf9e4)

    def update(self, points: int, time: int, moves: int) -> None:
        """
        Update the HUD.
        """
        if self._gametype is None:
            self._points_value.text = f'{points}'
            self._time_value.text = f'{time // 60}:{time % 60:02d}'
            self._moves_value.text = f'{moves}'
            self._moves_value.x = self._size[0] - self._moves_value.size[0]
            self._moves_title.x = self._size[0] - self._moves_title.size[0]
        elif self._gametype == 0:
            self._time_value.text = f'{time // 60}:{time % 60:02d}'
        elif self._gametype == 1:
            self._time_value.text = f'{moves}'
        elif self._gametype == 2:
            self._time_value.text = f'{points}'

        self._time_value.x = self._size[0] / 2 - self._time_value.size[0] / 2
        self._time_title.x = self._size[0] / 2 - self._time_title.size[0] / 2

    def set_titles(self, points: str, time: str, moves: str) -> None:
        """
        Change title strings.
        """
        self._points_title.text = points
        self._time_title.text = time
        self._moves_title.text = moves
