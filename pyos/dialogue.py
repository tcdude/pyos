"""
Provides a rudimentary dialogue UI element. Probably will find its way into
foolysh.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple

from foolysh.ui import label, button

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
class DialogueButton:
    """Representation of a button used in a Dialogue."""
    text: str
    fmtkwargs: Dict[str, Any] = None
    callback: Callable = None
    cbargs: Tuple[Any, ...] = ()
    cbkwargs: Dict[str, Any] = None


class Dialogue(label.Label):
    """Provides a dialogue with variable amounts of buttons."""
    def __init__(self, text: str, buttons: Tuple[DialogueButton, ...],
                 **kwargs) -> None:
        if text.find('\n') > -1:
            kwargs['multiline'] = True
        super().__init__(text=text, **kwargs)
        self.__buttons: List[button.Button] = []
        for dbut in buttons:
            if dbut.fmtkwargs is None:
                dbut.fmtkwargs = {}
            but = button.Button(text=dbut.text, **dbut.fmtkwargs)
            if dbut.callback is not None:
                if dbut.cbkwargs is None:
                    dbut.cbkwargs = {}
                but.onclick(dbut.callback, *dbut.cbargs, **dbut.cbkwargs)
            else:
                Warning('Added a button to the Dialogue without callback!')
            but.reparent_to(self)
            self.__buttons.append(but)

    def _update(self):
        width = sum([i.size[0] for i in self.__buttons])
        margin = (width * 1.1 - width) / max(len(self.__buttons) - 1, 1)
        width *= 1.1
        pos_x = max(self.border_thickness, self.corner_radius)
        pos_y = self.size[1] - pos_x * 1.1 - self.__buttons[0].size[1]
        pos_x += (self.size[0] - width) / 2 - pos_x / 2
        for but in self.__buttons:
            but.pos = pos_x, pos_y
            pos_x += but.size[0] + margin
        super()._update()
