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
__version__ = '0.2'


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

    def update(self, points: int, time: int, moves: int) -> None:
        """
        Update the HUD.
        """
        self._points_value.text = f'{points}'
        self._time_value.text = f'{time // 60}:{time % 60:02d}'
        self._time_value.x = self._size[0] / 2 - self._time_value.size[0] / 2
        self._time_title.x = self._size[0] / 2 - self._time_title.size[0] / 2
        self._moves_value.text = f'{moves}'
        self._moves_value.x = self._size[0] - self._moves_value.size[0]
        self._moves_title.x = self._size[0] - self._moves_title.size[0]

    def set_titles(self, points: str, time: str, moves: str) -> None:
        """
        Change title strings.
        """
        self._points_title.text = points
        self._time_title.text = time
        self._moves_title.text = moves
