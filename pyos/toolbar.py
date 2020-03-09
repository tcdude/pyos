"""
Provide the ToolBar class.
"""

from typing import Tuple
from typing import Type

from foolysh.scene import node
from foolysh.tools import vec2

import common

__author__ = 'Tiziano Bettio'
__copyright__ = """
Copyright (c) 2019 Tiziano Bettio

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


class ToolBar:
    """Class for holding the ToolBar."""
    # pylint: disable=too-many-instance-attributes

    def __init__(
            self,
            parent: Type[node.Node],
            size: Tuple[float, float],
            font: str
        ) -> None:
        self._size = size
        self._background = parent.attach_image_node(image=common.BOTTOM_BAR_IMG)
        self._background.depth = 500
        self._new_icon = self._background.attach_text_node(
            'New Icon',
            chr(0xf893),
            font,
            size[1] * 0.9
        )
        self._new_text = self._background.attach_text_node(
            'New Text',
            'Deal',
            font,
            size[1] * 0.5
        )
        self._reset_icon = self._background.attach_text_node(
            'Reset Icon',
            chr(0xf021),
            font,
            size[1] * 0.9
        )
        self._reset_text = self._background.attach_text_node(
            'Reset Text',
            'Reset',
            font,
            size[1] * 0.5
        )
        self._undo_icon = self._background.attach_text_node(
            'Undo Icon',
            chr(0xfa4b),
            font,
            size[1] * 0.9
        )
        self._undo_text = self._background.attach_text_node(
            'Undo Text',
            'Undo',
            font,
            size[1] * 0.5
        )

    @property
    def new_deal(self) -> Tuple[node.TextNode, node.TextNode]:
        """Tuple of the "new deal" icon and text nodes."""
        return self._new_icon, self._new_text

    @property
    def reset(self) -> Tuple[node.TextNode, node.TextNode]:
        """Tuple of the "reset" icon and text nodes."""
        return self._reset_icon, self._reset_text

    @property
    def undo(self) -> Tuple[node.TextNode, node.TextNode]:
        """Tuple of the "undo" icon and text nodes."""
        return self._undo_icon, self._undo_text

    def click_area(self, mouse_pos: vec2.Vec2) -> str:
        """
        Returns the clicked area ('new', 'reset', 'undo') or an empty string.
        """
        m_x, m_y = mouse_pos.x, mouse_pos.y
        if not self._background.aabb.inside_tup(m_x, m_y):
            return ''
        if self._new_icon.aabb.inside_tup(m_x, m_y) or \
              self._new_text.aabb.inside_tup(m_x, m_y):
            return 'new'
        if self._reset_icon.aabb.inside_tup(m_x, m_y) or \
              self._reset_text.aabb.inside_tup(m_x, m_y):
            return 'reset'
        if self._undo_icon.aabb.inside_tup(m_x, m_y) or \
              self._undo_text.aabb.inside_tup(m_x, m_y):
            return 'undo'
        return ''

    def update(self) -> None:
        """
        Update the TaskBar placement.
        """
        i_w, i_h = self._new_icon.size
        i_y = -i_h * .175
        _, t_h = self._new_text.size
        t_y = (self._size[1] - t_h) * 0.25
        self._new_icon.pos = i_w * 0.2, i_y
        self._new_text.pos = i_w * 1.3, t_y

        i_w, _ = self._reset_icon.size
        t_w, _ = self._reset_text.size
        width = i_w * 1.2 + t_w
        i_x = self._size[0] / 2 - width / 2
        self._reset_icon.pos = i_x, i_y
        self._reset_text.pos = i_x + i_w * 1.2, t_y

        i_w, _ = self._undo_icon.size
        t_w, _ = self._undo_text.size
        width = i_w * 1.4 + t_w
        i_x = self._size[0] - width
        self._undo_icon.pos = i_x, i_y
        self._undo_text.pos = i_x + i_w * 1.2, t_y
