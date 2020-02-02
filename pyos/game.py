"""
Ad free simple Solitaire implementation.
"""

from dataclasses import dataclass
import logging
import os
from typing import Union

import sdl2
from foolysh.app import App
from foolysh.tools.vector2 import Vector2

import common
from hud import HUD
from table import Table
from table_layout import TableLayout
from toolbar import ToolBar

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


@dataclass
class DragInfo:
    """Retains info for a subsequent call to Table methods."""
    pile_id: int
    num_cards: int
    start_area: common.TableArea


class Game(App):
    """
    Entry point of the App.
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        super().__init__(config_file='.foolysh/foolysh.ini')

        # Layout / Cards
        self.__table_layout: Union[None, TableLayout] = None
        self.__hud: Union[None, HUD] = None
        self.__tool_bar: Union[None, ToolBar] = None
        self._setup_layout()

        # State
        self.__table = Table(self.__table_layout.callback)
        self.__table_layout.set_table(self.__table)
        self.__valid_drop = False
        self.__last_window_size = 0, 0
        self.__refresh_next_frame = 0
        self.__last_auto = 0.0
        self.__last_undo = False
        self.__mouse_down_pos = Vector2()
        self.__drag_info: DragInfo = DragInfo(-1, -1, common.TableArea.STACK)

        # Events / Tasks
        self._setup_events_tasks()

        # Logging
        common.setup_dict_config(self.config['pyos']['log_level'])
        self.log.info('pyos started')
        self._load()

    # Properties

    @property
    def log(self):
        """The logger."""
        return logging

    # Setup

    def _setup_events_tasks(self):
        """Setup Events and Tasks."""
        self.event_handler.listen(
            'quit',
            sdl2.SDL_QUIT,
            self.quit,
            0,
            blocking=False
        )
        self.event_handler.listen(
            'android_back',
            sdl2.SDL_KEYUP,
            self._back
        )
        if self.isandroid:
            self.event_handler.listen(
                'finger_down',
                sdl2.SDL_FINGERDOWN,
                self._mouse_down,
                -5  # make sure it runs after drag_drop.
            )
            self.event_handler.listen(
                'finger_up',
                sdl2.SDL_FINGERUP,
                self._mouse_up,
                -5
            )
            self.event_handler.listen(
                'APP_TERMINATING',
                sdl2.SDL_APP_TERMINATING,
                self.quit,
                0,
                blocking=False
            )
            self.event_handler.listen(
                'APP_WILLENTERBACKGROUND',
                sdl2.SDL_APP_WILLENTERBACKGROUND,
                self._event_will_enter_bg
            )
            self.event_handler.listen(
                'APP_DIDENTERBACKGROUND',
                sdl2.SDL_APP_DIDENTERBACKGROUND,
                self._event_pause
            )
            self.event_handler.listen(
                'APP_LOWMEMORY',
                sdl2.SDL_APP_LOWMEMORY,
                self._event_low_memory
            )
        else:
            self.event_handler.listen(
                'mouse_down',
                sdl2.SDL_MOUSEBUTTONDOWN,
                self._mouse_down,
                -5  # make sure it runs after drag_drop.
            )
            self.event_handler.listen(
                'mouse_up',
                sdl2.SDL_MOUSEBUTTONUP,
                self._mouse_up,
                -5  # make sure it runs after drag_drop.
            )
        self.task_manager.add_task('HUD_Update', self._update_hud, 0.05)
        self.task_manager.add_task('auto_save', self._auto_save_task, 5, False)
        self.task_manager.add_task(
            'auto_complete',
            self._auto_foundation,
            0.05
        )
        self.task_manager.add_task(
            'layout_process',
            self.__table_layout.process,
            0
        )

    def _setup_layout(self):
        """One time setup of the scene."""
        self.__table_layout = TableLayout(
            float(self.config['pyos']['card_ratio']),
            float(self.config['pyos']['padding']),
            tuple(
                [
                    float(i)
                    for i in self.config['pyos']['status_size'].split(',')
                ]
            ),
            tuple(
                [
                    float(i)
                    for i in self.config['pyos']['toolbar_size'].split(',')
                ]
            )
        )
        self.__table_layout.root.reparent_to(self.root)

        self.__hud = HUD(
            self.__table_layout.status,
            tuple(
                [
                    float(i)
                    for i in self.config['pyos']['status_size'].split(',')
                ]
            ),
            self.config['font']['normal'],
            self.config['font']['bold']
        )

        self.__tool_bar = ToolBar(
            self.__table_layout.toolbar,
            tuple(
                [
                    float(i)
                    for i in self.config['pyos']['toolbar_size'].split(',')
                ]
            ),
            self.config['font']['normal']
        )

        for suit in range(4):
            for value in range(13):
                k = suit, value
                self.drag_drop.enable(
                    self.__table_layout.get_card(k),
                    self._drag_cb,
                    (k, ),
                    self._drop_cb,
                    (k, )
                )

    # Tasks / Events

    def _auto_save_task(self):
        """Auto save task."""
        if not self.__table.is_paused:
            self.log.debug('Auto Save')
            self._save()

    def _auto_foundation(self, dt):
        """Task to auto solve a game."""
        # pylint: disable=invalid-name, unused-argument
        if self.__table.is_paused or self.__last_undo:
            return
        if self.config.getboolean('pyos', 'auto_flip', fallback=False):
            for i in range(7):
                self.__table.flip(i)
        auto_solve = self.config.getboolean(
            'pyos',
            'auto_solve',
            fallback=False
        )
        if self.__table.win_condition:
            self.__refresh_next_frame = 2
            self.__table.pause()
        elif auto_solve and self.__table.solved:
            self._auto_solve()

    def _auto_solve(self):
        """When solved, determines and executes the next move."""
        call_time = self.clock.get_time()
        if call_time - self.__last_auto < self.config.getfloat(
                'pyos', 'auto_solve_delay', fallback=0.3):
            return
        if self.config.getboolean(
                'pyos',
                'waste_to_foundation',
                fallback=False):
            meths = (
                self.__table.tableau_to_foundation,
                self.__table.waste_to_foundation,
                self.__table.waste_to_tableau,
                self.__table.draw
            )
        else:
            meths = (
                self.__table.tableau_to_foundation,
                self.__table.waste_to_tableau,
                self.__table.waste_to_foundation,
                self.__table.draw
            )
        for meth in meths:
            if meth():
                self.__last_auto = call_time
                return
        raise RuntimeError('Unhandled exception.')

    def _update_hud(self, dt):
        """Update HUD."""
        # pylint: disable=invalid-name,unused-argument
        if self.window.size != self.__last_window_size:
            self.__last_window_size = self.window.size
            self.__table_layout.setup(
                self.__last_window_size,
                self.config.getboolean('pyos', 'left_handed')
            )
            self.__refresh_next_frame = 2
        elif self.__refresh_next_frame > 0:
            self.__refresh_next_frame -= 1
            self.__table.refresh_table()
            # self.__table_layout.refresh_all()
            self.log.debug('refresh_table')
        moves, elapsed_time, points = self.__table.stats
        self.__hud.update(points, int(round(elapsed_time, 0)), moves)
        self.__tool_bar.update()

    def _event_pause(self, event=None):
        """Called when the app enters background."""
        # pylint: disable=unused-argument
        self.log.info('Paused game')
        self.__table.pause()

    def _event_will_enter_bg(self, event=None):
        """Called when the os announces that the app will enter background."""
        # pylint: disable=unused-argument
        self.log.warning('Unhandled event APP_WILLENTERBACKGROUND!!!')

    def _event_low_memory(self, event=None):
        """Called when the os announces low memory."""
        # pylint: disable=unused-argument
        self.log.warning('Unhandled event APP_LOWMEMORY!!!')

    def _back(self, event):
        """Handles Android Back, Escape and Backspace Events"""
        if event.key.keysym.sym in (
                sdl2.SDLK_AC_BACK, 27, sdl2.SDLK_BACKSPACE):
            self.quit(blocking=False)

    def on_quit(self):
        """Overridden on_quit event to make sure the state is saved."""
        self.log.info('Saving state and quitting pyos')
        self._save()

    def _drag_cb(self, k) -> bool:
        """Callback on start drag of a card."""
        table_click = self.__table_layout.click_area(self.mouse_pos)
        if table_click is None or table_click[0] == common.TableArea.STACK or \
              self.__table_layout.get_card(k).index == 1:
            return False
        self.__drag_info.start_area = table_click[0]
        if table_click[0] == common.TableArea.TABLEAU:
            pile_id = table_click[1][0]
            card_id = table_click[1][1]
            if len(self.__table.table.tableau[pile_id]) < card_id + 1:
                return False
            self.__table_layout.on_drag(
                self.__table.table.tableau[pile_id][card_id].index[0],
                [
                    i.index[0]
                    for i in self.__table.table.tableau[pile_id][card_id + 1:]
                ]
            )
            self.__drag_info.pile_id = pile_id
            num_cards = len(self.__table.table.tableau[pile_id]) - card_id
            self.__drag_info.num_cards = num_cards
        elif table_click[0] == common.TableArea.FOUNDATION:
            self.__drag_info.pile_id = table_click[1][0]
            self.__drag_info.num_cards = 1
            self.__table_layout.on_drag(
                self.__table.table.foundation[table_click[1][0]][-1].index[0]
            )
        else:  # WASTE
            self.__drag_info.pile_id = -1
            self.__drag_info.num_cards = 1
            self.__table_layout.on_drag(
                self.__table.table.waste[-1].index[0]
            )
        return True

    def _drop_cb(self, k):
        """Callback on drop of a card."""
        self.__table_layout.on_drop()
        waste_tableau = common.TableArea.WASTE, common.TableArea.TABLEAU
        if self.__drag_info.start_area in waste_tableau:
            if not self._drop_foundation(k):
                self._drop_tableau(k)
        elif self.__drag_info.start_area == common.TableArea.FOUNDATION:
            self._drop_tableau(k)
        self.__refresh_next_frame = 1
        self.__valid_drop = True

    # Drop helper methods

    def _drop_foundation(self, k):
        """Evaluates a drop on foundation"""
        for i, t_node in enumerate(self.__table_layout.foundation):
            if t_node.aabb.overlap(self.__table_layout.get_card(k).aabb):
                if self.__drag_info.start_area == common.TableArea.WASTE:
                    if self.__table.waste_to_foundation(i):
                        return True
                elif self.__drag_info.start_area == common.TableArea.TABLEAU:
                    if self.__table.tableau_to_foundation(
                            self.__drag_info.pile_id, i):
                        return True
        return False

    def _drop_tableau(self, k):
        """Evaluates a drop on tableau"""
        tableau = self.__table.table.tableau
        t2t_move = self.__drag_info.start_area == common.TableArea.TABLEAU
        w2t_move = self.__drag_info.start_area == common.TableArea.WASTE
        f2t_move = self.__drag_info.start_area == common.TableArea.FOUNDATION
        res = False
        for i, t_node in enumerate(self.__table_layout.tableau):
            if not tableau[i]:
                if k[1] == 12:  # King special case
                    check_aabb = self.__table_layout.get_card(k).aabb
                    if t_node.aabb.overlap(check_aabb):
                        if t2t_move and self.__table.tableau_to_tableau(
                                self.__drag_info.pile_id,
                                i,
                                self.__drag_info.num_cards):
                            res = True
                            break
                        if w2t_move and self.__table.waste_to_tableau(i):
                            res = True
                            break
                        if f2t_move and self.__table.foundation_to_tableau(
                                self.__drag_info.pile_id,
                                i):
                            res = True
                            break
                continue
            check_aabb = self.__table_layout.get_card(
                tableau[i][-1].index[0]
            ).aabb
            if check_aabb.overlap(self.__table_layout.get_card(k).aabb):
                if t2t_move and self.__table.tableau_to_tableau(
                        self.__drag_info.pile_id,
                        i,
                        self.__drag_info.num_cards):
                    res = True
                    break
                if w2t_move and self.__table.waste_to_tableau(i):
                    res = True
                    break
                if f2t_move and self.__table.foundation_to_tableau(
                        self.__drag_info.pile_id,
                        i):
                    res = True
                    break
        return res

    def _mouse_down(self, event):
        """
        Global mouse down event to register mouse position when a click starts.
        """
        # pylint: disable=unused-argument
        self.__mouse_down_pos = self.mouse_pos

    def _mouse_up(self, event):
        """
        Global mouse up event.
        """
        # pylint: disable=unused-argument
        if self.__valid_drop:  # Event is handled by dragdrop.
            self.__valid_drop = False
            return
        self.__table_layout.on_drop()
        self.__last_undo = False
        # Check click threshold
        up_down_length = (self.__mouse_down_pos - self.mouse_pos).length
        click_threshold = self.config.getfloat(
            'pyos',
            'click_threshold',
            fallback=0.05
        )
        if up_down_length > click_threshold:
            self.log.debug('click_threshold reached.')
            return

        table_click = self.__table_layout.click_area(self.mouse_pos)
        if table_click is not None:
            self.log.info(f'Table: {repr(table_click)}')
            self._table_click(table_click)
            return

        tool_bar_click = self.__tool_bar.click_area(self.mouse_pos)
        if tool_bar_click != '':
            self.log.info(f'Toolbar: {tool_bar_click}')
            if tool_bar_click == 'new':
                self._new_deal()
            elif tool_bar_click == 'reset':
                self._reset_deal()
            elif tool_bar_click == 'undo':
                self._undo_move()
                self.__last_undo = True

    # Click helper methods

    def _table_click(self, table_click):
        """Evaluates possible moves for table clicks."""
        if table_click[0] == common.TableArea.STACK:
            self.__table.draw()
        elif table_click[0] == common.TableArea.WASTE:
            if self.config.getboolean(
                    'pyos', 'waste_to_foundation', fallback=False):
                if not self.__table.waste_to_foundation():
                    self.__table.waste_to_tableau()
            else:
                if not self.__table.waste_to_tableau():
                    self.__table.waste_to_foundation()
        elif table_click[0] == common.TableArea.FOUNDATION:
            self.__table.foundation_to_tableau(table_click[1][0])
        else:  # TABLEAU
            from_pile = self.__table.table.tableau[table_click[1][0]]
            num_cards = len(from_pile) - table_click[1][1]
            if num_cards == 1 and self.__table.flip(table_click[1][0]):
                return
            if num_cards == 1 and self.__table.tableau_to_foundation(
                    table_click[1][0]):
                return
            if self.__table.tableau_to_tableau(
                    from_pile=table_click[1][0], num_cards=num_cards):
                return

    # Game State

    def _save(self):
        path = os.path.join(
            self.config['base']['cache_dir'],
            self.config['pyos']['state_file']
        )
        with open(path, 'wb') as f_handler:
            f_handler.write(self.__table.get_state(pause=False))

    def _load(self):
        path = os.path.join(
            self.config['base']['cache_dir'],
            self.config['pyos']['state_file']
        )
        if os.path.isfile(path):
            with open(path, 'rb') as f_handler:
                self.__table.set_state(f_handler.read())
            self.__refresh_next_frame = 2

    def _show_score(self):
        """Show the result screen."""

    # Interaction

    def _flip_cards(self):
        """Flip closed cards if so configured."""

    def _undo_move(self):
        """On Undo click: Undo the last move."""
        self.__table.undo()

    def _reset_deal(self):
        """On Reset click: Reset the current game to start."""
        self.__table.reset()
        self.__refresh_next_frame = 2

    def _new_deal(self):
        """On New Deal click: Deal new game."""
        self.__table.deal()
        self.__refresh_next_frame = 2
