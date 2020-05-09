"""
Provide the ToolBar class.
"""

from dataclasses import dataclass
from typing import Callable, Tuple, Type, Union

from foolysh.scene import node
from foolysh.ui import frame, button

import common

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
class ToolBarButtons:
    """The buttons in the toolbar."""
    new: button.Button
    reset: button.Button
    undo: button.Button
    menu: button.Button
    giveup: button.Button


class ToolBar:
    """Class for holding the ToolBar."""
    def __init__(self, parent: Type[node.Node], size: Tuple[float, float],
                 font: str, callbacks: Tuple[Callable, ...]) -> None:
        border = size[1] / 20
        radius = size[1] / 3
        self._frame = frame.Frame(name='toolbar background', size=size,
                                  frame_color=common.TOOLBAR_FRAME_COLOR,
                                  border_thickness=border,
                                  border_color=common.TOOLBAR_BORDER_COLOR,
                                  corner_radius=radius, multi_sampling=2,
                                  alpha=180)
        self._frame.reparent_to(parent)
        self._frame.pos = -size[0] / 2, -size[1] * 1.1
        self._buttons: Union[None, ToolBarButtons] = None
        self._setup_buttons(size, border, radius, font, callbacks)

    def hide(self):
        """Hide the toolbar."""
        self._frame.hide()

    def show(self):
        """Show the toolbar."""
        self._frame.show()

    def toggle(self, normal: bool = True) -> None:
        """Toggle the new deal/give up buttons. Default shows new deal."""
        if normal:
            self._buttons.giveup.hide()
            self._buttons.new.show()
        else:
            self._buttons.giveup.show()
            self._buttons.new.hide()

    def _setup_buttons(self, size, border, radius, font, callbacks):
        # pylint: disable=too-many-arguments,too-many-locals

        offset = max(border, radius)
        unit_width = (size[0] - 2 * offset) / 10.6
        height = size[1] - border * 6
        font_size = (height - border * 2) * 0.58
        kwargs = common \
            .get_toolbar_btn_kw(font=font, font_size=font_size,
                                border_thickness=height / 20,
                                down_border_thickness=border * 1.1,
                                corner_radius=min(height, unit_width) / 2)
        newb = button.Button(name='new but', size=(unit_width * 3, height),
                             text=common.NEW_SYM + ' Deal', **kwargs)
        newb.reparent_to(self._frame)
        newb.onclick(callbacks[0])
        newb.pos = offset, (size[1] - height) / 2
        giveup = button.Button(name='new but', size=(unit_width * 3, height),
                               text=common.GUP_SYM + 'Give Up', **kwargs)
        giveup.reparent_to(self._frame)
        giveup.onclick(callbacks[4])
        giveup.pos = offset, (size[1] - height) / 2
        giveup.hide()
        offset += unit_width * 3.2

        reset = button.Button(name='reset but', size=(unit_width * 3, height),
                              text=common.RES_SYM + ' Retry', **kwargs)
        reset.reparent_to(self._frame)
        reset.onclick(callbacks[1])
        reset.pos = offset, (size[1] - height) / 2
        offset += unit_width * 3.2

        undo = button.Button(name='undo but', size=(unit_width * 3, height),
                             text=common.UNDO_SYM + ' Undo', **kwargs)
        undo.reparent_to(self._frame)
        undo.onclick(callbacks[2])
        undo.pos = offset, (size[1] - height) / 2
        offset += unit_width * 3.2

        kwargs['font_size'] *= 1.25
        kwargs['border_thickness'] = 0
        menu = button.Button(name='menu but', size=(unit_width, height),
                             text=common.MENU_SYM, **kwargs)
        menu.reparent_to(self._frame)
        menu.onclick(callbacks[3])
        menu.pos = offset, (size[1] - height) / 2
        self._buttons = ToolBarButtons(newb, reset, undo, menu, giveup)
