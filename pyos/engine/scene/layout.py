"""
Provides various classes to aide with Layout of an app.
"""
from typing import Iterable
from typing import Optional
from typing import Tuple
from typing import Union

from . import nodepath

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


def compute_spacing(spacing_arg):
    if spacing_arg is None:
        arg_count = 1
        spacing = [1.0]
    elif isinstance(spacing_arg, (list, tuple)) and len(spacing_arg) == 1 and \
            isinstance(spacing_arg[0], int) and spacing_arg[0] > 0:
        arg_count = spacing_arg[0]
        spacing = [1.0 / arg_count] * arg_count
    elif isinstance(spacing_arg, (list, tuple)) and len(spacing_arg) > 1:
        arg_count = len(spacing_arg)
        none_count = spacing_arg.count(None)
        if none_count:
            known_space = sum([i for i in spacing_arg if i is not None])
            e = 0
            while 10 ** e < known_space:
                e += 1
            total_space = 10 ** e
            f = 1.0 / total_space
            none_space = ((total_space - known_space) / none_count) * f
            spacing = [none_space if i is None else i * f for i in spacing_arg]
        else:
            f = 1.0 / sum(spacing_arg)
            spacing = [i * f for i in spacing_arg]
    else:
        raise ValueError
    return arg_count, spacing


class GridLayout(object):
    """
    Provides a grid layout as collection of NodePaths distributed inside the
    specified ``box`` to indicate the top left and bottom right extent of the
    grid, relative to the ``parent`` NodePath.

    :param parent: ``NodePath``
    :param box: ``Tuple[float, float, float, float]`` -> indicating top left and
        bottom right points of the grid in world space units.
    :param rows: Optional ``iterable`` -> row sizes or number of rows if length
        is 1.
    :param cols: Optional ``iterable`` -> column sizes or number of columns if
        length is 1.
    :param margins: Optional ``Tuple[float, float]`` -> cell margin in world
        space units.

    Example usage:

    >>> parent_np = nodepath.NodePath()
    >>> grid = GridLayout(parent_np, (0.0, 0.0, 1.7, 1.0), rows=(10, None, 20))
    >>> content_node_path = nodepath.NodePath('Cell [0, 0]', parent=grid[1])
    >>> grid[1]
    NodePath(GridCell(1, 0))

    .. note::
        The following rules apply to the parameters ``rows`` and ``cols``:

        * If ``None`` is passed (as is by default), exactly 1 row/column is created.
        * If an ``iterable`` of length 1 is passed, it indicates the number of equally sized rows/columns as positive ``int``.
        * ``None`` inside an ``iterable`` will be interpreted as equal part of the remaining space.
        * The remaining space for the example above is calculated ``100 - 10 - 20 = 70``
        * Total space is the next higher power of 10 from the sum of all numerical values in an ``iterable``
        * For an ``iterable`` containing only numerical values the sum of all values reflects ``100%``

    """
    def __init__(
            self,
            parent,             # type: nodepath.NodePath
            box,                # type: Tuple[NUM, NUM, NUM, NUM]
            rows=None,          # type: Optional[Union[Iterable, None]]
            cols=None,          # type: Optional[Union[Iterable, None]]
            margins=(0.0, 0.0)  # type: Optional[Tuple[float, float]]
    ):
        # type: (...) -> None
        if not isinstance(box, tuple):
            raise TypeError('expected Tuple[float, float, float, float] for '
                            'argument box')
        if len(box) != 4 or sum(
                [isinstance(i, (int, float)) for i in box]) != 4:
            raise ValueError('expected Tuple[float, float, float, float] for '
                             'argument box')
        if box[0] >= box[2] or box[1] >= box[3]:
            raise ValueError('invalid box, expected (x1, y1, x2, y2) where '
                             'x1 < x2 and y1 < y2.')
        try:
            row_count, row_spacing = compute_spacing(rows)
        except ValueError:
            raise ValueError('expected rows to be one of None, Iterable '
                             'containing either a single positive int or a '
                             'combination of positive int/float and optionally '
                             'None.')
        try:
            col_count, col_spacing = compute_spacing(cols)
        except ValueError:
            raise ValueError('expected cols to be one of None, Iterable '
                             'containing either a single positive int or a '
                             'combination of positive int/float and optionally '
                             'None.')

        self._root = parent.attach_new_node_path(f'GridLayout({row_count}, '
                                                 f'{col_count})')
        self._root.center = nodepath.TOP_LEFT
        size = (box[2] - box[0], box[3] - box[1])
        self._root.set_dummy_size(size)
        self._root.position = box[:2]
        self._cells = []
        y_start = box[1]
        for row_id, row_space in enumerate(row_spacing):
            self._cells.append([])
            r_dist = row_space * size[1]
            if r_dist <= margins[1] * 2:
                raise ValueError('row margins are equal or larger in size than '
                                 f'the row with index {row_id}')
            y_end = y_start + r_dist
            x_start = box[0]
            for col_id, col_space in enumerate(col_spacing):
                np = self._root.attach_new_node_path(f'GridCell({row_id}, '
                                                     f'{col_id})')
                c_dist = col_space * size[0]
                if c_dist <= margins[0] * 2:
                    raise ValueError(f'column margins are equal or larger in '
                                     f'size than the column with index '
                                     f'{col_id}')
                np.set_dummy_size(
                    (c_dist - 2 * margins[0], r_dist - 2 * margins[1])
                )
                x_end = x_start + c_dist
                np.position = x_start + margins[0], y_start + margins[1]
                x_start = x_end
                self._cells[-1].append(np)
            y_start = y_end

    def __getitem__(self, item):
        if isinstance(item, tuple):
            if len(item) == 2:
                if isinstance(item[0], int) and isinstance(item[1], int):
                    return self._cells[item[0]][item[1]]
            raise IndexError('expected Tuple[int, int]')
        elif isinstance(item, int) and len(self._cells) == 1:
            return self._cells[0][item]
        elif isinstance(item, int) and len(self._cells[0]) == 1:
            return self._cells[item][0]
        else:
            raise IndexError('invalid index, expected either Tuple[int, int] '
                             'or int in the case of a grid with either a '
                             'single row or column')

    def reparent_to(self, new_parent):
        # type: (nodepath.NodePath) -> bool
        return self._root.reparent_to(new_parent)
