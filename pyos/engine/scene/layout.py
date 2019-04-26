"""
Provides various classes to aide with Layout of an app.
"""

from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from . import nodepath
from ..tools import vector

__author__ = 'Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'
__copyright__ = """Copyright (c) 2019 Tiziano Bettio

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
SOFTWARE."""

# types
NUM = Union[int, float]


class GridLayout(object):
    """
    Provides a grid layout as collection of NodePaths distributed inside the
    specified ``box`` to indicate the top left and bottom right extent of the
    grid, relative to the ``parent`` NodePath.

    :param parent: NodePath
    :param box: 4-tuple indicating top left and bottom right points of the grid
    :param rows: Optional list or tuple of row sizes
    :param cols: Optional list or tuple of column sizes
    :param margins: Optional 2-tuple as margin of the cells

    Example usage:

    >>> parent_np = nodepath.NodePath()
    >>> grid = GridLayout(parent_np, (0.0, 0.0, 1.7, 1.0), rows=(10, None, 20))
    >>> content_node_path = nodepath.NodePath('Cell [0, 0]', parent=grid[1])
    >>> grid[1].position
    ... vector.Point(0.0000, 0.1000)

    """
    def __init__(
            self,
            parent,             # type: nodepath.NodePath
            box,                # type: Tuple[NUM, NUM, NUM, NUM]
            rows=None,          # type: Optional[Union[List[NUM], tuple]]
            cols=None,          # type: Optional[Union[List[NUM], tuple]]
            margins=(0.0, 0.0)  # type: Optional[Tuple[float, float]]
    ):
        # type: (...) -> None
        self.__root = parent.attach_new_node_path(f'GridLayout({str(rows)}, '
                                                  f'{str(cols)})')

    def __getitem__(self, item):
        pass

    def reparent_to(self, new_parent):
        # type: (nodepath.NodePath) -> bool
        return self.__root.reparent_to(new_parent)
