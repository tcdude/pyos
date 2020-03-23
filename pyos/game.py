"""
Ad free simple Solitaire implementation.
"""

from dataclasses import dataclass
import os
import random
from typing import Tuple, Union

from loguru import logger
import sdl2
from foolysh.animation import DepthInterval, BlendType, PosInterval, Sequence \
                              , RotationInterval
from foolysh.tools.vec2 import Vec2

import app
import common
from dialogue import Dialogue, DialogueButton
from hud import HUD
from table import Table
from table_layout import TableLayout
from toolbar import ToolBar

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


@dataclass
class DragInfo:
    """Retains info for a subsequent call to Table methods."""
    pile_id: int
    num_cards: int
    start_area: common.TableArea


@dataclass
class GameSystems:
    """Holds all the various systems."""
    game_table: Table
    layout: TableLayout
    hud: HUD
    toolbar: ToolBar
    windlg: Union[None, Dialogue] = None


@dataclass
class GameState:
    """Holds various state attributes."""
    # pylint: disable=too-many-instance-attributes

    valid_drop: bool = False
    last_window_size: Tuple[int, int] = (0, 0)
    refresh_next_frame: int = 0
    last_auto: float = 0.0
    last_undo: bool = False
    mouse_down_pos: Vec2 = Vec2()
    drag_info: DragInfo = DragInfo(-1, -1, common.TableArea.STACK)
    fresh_state: bool = True
    day_deal: bool = True


class Game(app.AppBase):
    """
    Entry point of the App.
    """
    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.__systems: Union[None, GameSystems] = None
        self.__state: GameState = GameState()
        self.__need_setup: bool = True
        self.__active: bool = False
        logger.info('Game initialized.')

    # State
    def enter_game(self):
        """Tasks to be performed when this state is activated."""
        logger.debug('Enter state game')
        self.__setup()
        self.__state.fresh_state = True
        if self.need_new_game or self.stats.first_launch \
              or self.daydeal is not None:
            self.__new_deal()

    def exit_game(self):
        """Tasks to be performed when this state is left."""
        logger.debug('Exit state game')
        self.__disable_all()
        dlg = self.__systems.windlg
        if dlg is not None and not dlg.hidden:
            dlg.hide()
        self.__systems.layout.root.hide()
        self.__systems.toolbar.hide()
        self.__systems.game_table.pause()
        self.__save()

    # Setup / Tear down

    def __disable_all(self):
        if not self.__active:
            return
        self.event_handler.forget('mouse_down')
        self.event_handler.forget('mouse_up')
        self.task_manager.remove_task('HUD_Update')
        self.task_manager.remove_task('auto_save')
        self.task_manager.remove_task('auto_complete')
        self.task_manager.remove_task('layout_process')
        for suit in range(4):
            for value in range(13):
                k = suit, value
                self.drag_drop.disable(self.__systems.layout.get_card(k))
        self.__active = False

    def __setup(self):
        if self.__active:
            return
        self.__setup_layout()
        for suit in range(4):
            for value in range(13):
                k = suit, value
                self.drag_drop.enable(self.__systems.layout.get_card(k),
                                      self.__drag_cb, (k, ), self.__drop_cb,
                                      (k, ))
        self.__setup_events_tasks()
        self.__systems.layout.root.show()
        self.__systems.toolbar.show()
        self.__load()
        self.__systems.game_table.pause()
        self.__active = True

    def __setup_events_tasks(self):
        """Setup Events and Tasks."""
        if self.isandroid:
            down = sdl2.SDL_FINGERDOWN
            upe = sdl2.SDL_FINGERUP
        else:
            down = sdl2.SDL_MOUSEBUTTONDOWN
            upe = sdl2.SDL_MOUSEBUTTONUP

        # make sure mouse events run after drag_drop
        self.event_handler.listen('mouse_down', down, self.__mouse_down,
                                  priority=-5)
        self.event_handler.listen('mouse_up', upe, self.__mouse_up, priority=-5)

        self.task_manager.add_task('HUD_Update', self.__update_hud, 0.2)
        self.task_manager.add_task('auto_save', self.__auto_save_task, 5, False)
        self.task_manager.add_task('auto_complete', self.__auto_complete,
                                   0.05)
        self.task_manager.add_task('layout_process',
                                   self.__systems.layout.process, 0)

    def __setup_layout(self):
        """One time setup of the scene."""
        if not self.__need_setup:
            return
        stat_size = self.config['pyos']['status_size'].split(',')
        tool_size = self.config['pyos']['toolbar_size'].split(',')
        layout = TableLayout(self.config.getfloat('pyos', 'card_ratio'),
                             self.config.getfloat('pyos', 'padding'),
                             tuple([float(i) for i in stat_size]),
                             tuple([float(i) for i in tool_size]))
        layout.root.reparent_to(self.root)

        hud = HUD(layout.status, tuple([float(i) for i in stat_size]),
                  self.config['font']['normal'], self.config['font']['bold'])

        toolbar = ToolBar(self.ui.bottom_center,
                          tuple([float(i) for i in tool_size]),
                          self.config['font']['bold'],
                          (self.__new_deal, self.__reset_deal, self.__undo_move,
                           self.__menu))
        game_table = Table(layout.callback, self.shuffler)
        layout.set_table(game_table)
        self.__systems = GameSystems(game_table, layout, hud, toolbar)
        self.__need_setup = False

    # Tasks / Events

    def __auto_save_task(self):
        """Auto save task."""
        if not self.__systems.game_table.is_paused:
            logger.debug('Auto Save')
            self.__save()

    def __auto_complete(self, dt):
        """Task to auto solve a game."""
        # pylint: disable=invalid-name, unused-argument
        if not self.__active:
            return
        if self.__systems.game_table.is_paused or self.__state.last_undo:
            return
        if self.config.getboolean('pyos', 'auto_flip', fallback=False):
            for i in range(7):
                self.__systems.game_table.flip(i)
        auto_solve = self.config.getboolean('pyos', 'auto_solve',
                                            fallback=False)
        if auto_solve and self.__systems.game_table.solved \
              and not self.__systems.game_table.win_condition:
            self.__auto_solve()

    def __auto_solve(self):
        """When solved, determines and executes the next move."""
        call_time = self.clock.get_time()
        delay = self.config.getfloat('pyos', 'auto_solve_delay', fallback=0.25)
        if call_time - self.__state.last_auto < delay:
            return
        tbl = self.__systems.game_table
        if self.config.getboolean('pyos', 'waste_to_foundation',
                                  fallback=False):
            meths = (tbl.tableau_to_foundation, tbl.waste_to_foundation,
                     tbl.waste_to_tableau, tbl.draw)
        else:
            meths = (tbl.tableau_to_foundation, tbl.waste_to_tableau,
                     tbl.waste_to_foundation, tbl.draw)
        for meth in meths:
            if meth():
                self.__state.last_auto = call_time
                self.__update_attempt()
                return
        raise RuntimeError('Unhandled exception.')

    def __update_hud(self, dt):
        """Update HUD."""
        # pylint: disable=invalid-name,unused-argument
        if self.window.size != self.__state.last_window_size \
              or self.layout_refresh:
            self.__state.last_window_size = self.window.size
            self.__systems.layout.setup(self.__state.last_window_size,
                                        self.config.getboolean('pyos',
                                                               'left_handed'))
            self.__state.refresh_next_frame = 2
            self.layout_refresh = False
        elif self.__state.refresh_next_frame > 0:
            self.__state.refresh_next_frame -= 1
            self.__systems.game_table.refresh_table()
            logger.debug('refresh_table')
        moves, elapsed_time, points = self.__systems.game_table.stats
        self.__systems.hud.update(points, int(elapsed_time + 0.5), moves)
        if self.__systems.game_table.win_condition:
            self.__systems.layout.setup(self.__state.last_window_size,
                                        self.config.getboolean('pyos',
                                                               'left_handed'))
            self.__systems.layout.process(self.clock.get_dt())
            self.__systems.game_table.refresh_table()
            self.__state.refresh_next_frame = 2
            self.__systems.game_table.pause()
            self.__show_score()

    def __drag_cb(self, k) -> bool:
        """Callback on start drag of a card."""
        table_click = self.__systems.layout.click_area(self.mouse_pos)
        if table_click is None or table_click[0] == common.TableArea.STACK or \
              self.__systems.layout.get_card(k).index == 1:
            return False
        dragi = self.__state.drag_info
        tbl = self.__systems.game_table.table
        dragi.start_area = table_click[0]
        if table_click[0] == common.TableArea.TABLEAU:
            pile_id = table_click[1][0]
            card_id = table_click[1][1]
            pile = tbl.tableau[pile_id]
            if len(pile) < card_id + 1:
                return False
            self.__systems.layout \
                .on_drag(pile[card_id].index[0],
                         [i.index[0] for i in pile[card_id + 1:]])
            dragi.pile_id = pile_id
            num_cards = len(pile) - card_id
            dragi.num_cards = num_cards
        elif table_click[0] == common.TableArea.FOUNDATION:
            dragi.pile_id = table_click[1][0]
            dragi.num_cards = 1
            self.__systems.layout \
                .on_drag(tbl.foundation[table_click[1][0]][-1].index[0])
        else:  # WASTE
            dragi.pile_id = -1
            dragi.num_cards = 1
            self.__systems.layout.on_drag(tbl.waste[-1].index[0])
        return True

    def __drop_cb(self, k):
        """Callback on drop of a card."""
        self.__systems.layout.on_drop()
        waste_tableau = common.TableArea.WASTE, common.TableArea.TABLEAU
        invalid = False
        if self.__state.drag_info.start_area in waste_tableau:
            if not self.__drop_foundation(k):
                if not self.__drop_tableau(k):
                    invalid = True
        elif self.__state.drag_info.start_area == common.TableArea.FOUNDATION:
            if not self.__drop_tableau(k):
                invalid = True
        self.__state.refresh_next_frame = 1
        self.__state.valid_drop = True
        if invalid:
            self.__systems.game_table.invalid_move()
        else:
            self.__state.fresh_state = False
        self.__update_attempt()

    # Drop helper methods

    def __drop_foundation(self, k):
        """Evaluates a drop on foundation"""
        for i, t_node in enumerate(self.__systems.layout.foundation):
            if t_node.aabb.overlap(self.__systems.layout.get_card(k).aabb):
                if self.__state.drag_info.start_area == common.TableArea.WASTE:
                    if self.__systems.game_table.waste_to_foundation(i):
                        return True
                elif self.__state.drag_info.start_area == common.TableArea \
                      .TABLEAU:
                    if self.__systems.game_table.tableau_to_foundation(
                            self.__state.drag_info.pile_id, i):
                        return True
        return False

    def __drop_tableau(self, k):
        """Evaluates a drop on tableau"""
        tbl = self.__systems.game_table
        tableau = tbl.table.tableau
        dragi = self.__state.drag_info
        t2t_move = dragi.start_area == common.TableArea.TABLEAU
        w2t_move = dragi.start_area == common.TableArea.WASTE
        f2t_move = dragi.start_area == common.TableArea \
            .FOUNDATION
        res = False
        for i, t_node in enumerate(self.__systems.layout.tableau):
            pile_id = dragi.pile_id
            if not tableau[i]:
                if k[1] == 12:  # King special case
                    check_aabb = self.__systems.layout.get_card(k).aabb
                    if t_node.aabb.overlap(check_aabb):
                        res = tbl.tableau_to_tableau(pile_id, i,
                                                     dragi.num_cards)
                        if t2t_move and res:
                            res = True
                            break
                        res = tbl.waste_to_tableau(i)
                        if w2t_move and res:
                            res = True
                            break
                        res = tbl \
                            .foundation_to_tableau(pile_id, i)
                        if f2t_move and res:
                            res = True
                            break
                continue
            check_aabb = self.__systems.layout.get_card(tableau[i][-1].index[0])
            check_aabb = check_aabb.aabb
            if check_aabb.overlap(self.__systems.layout.get_card(k).aabb):
                if t2t_move and tbl.tableau_to_tableau(pile_id, i,
                                                       dragi.num_cards):
                    res = True
                    break
                if w2t_move and tbl.waste_to_tableau(i):
                    res = True
                    break
                if f2t_move and tbl.foundation_to_tableau(pile_id, i):
                    res = True
                    break
        return res

    def __mouse_down(self, event):
        """
        Global mouse down event to register mouse position when a click starts.
        """
        # pylint: disable=unused-argument
        self.__state.mouse_down_pos = self.mouse_pos

    def __mouse_up(self, event):
        """
        Global mouse up event.
        """
        # pylint: disable=unused-argument
        if self.__state.valid_drop:  # Event is handled by dragdrop.
            self.__state.valid_drop = False
            return
        self.__systems.layout.on_drop()
        self.__state.last_undo = False
        # Check click threshold
        up_down_length = (self.__state.mouse_down_pos - self.mouse_pos).length
        click_threshold = self.config.getfloat('pyos', 'click_threshold',
                                               fallback=0.05)
        if up_down_length > click_threshold:
            logger.debug(f'click_threshold reached -> dist={up_down_length}')
            return

        if self.config.getboolean('pyos', 'tap_move'):
            table_click = self.__systems.layout.click_area(self.mouse_pos)
            if table_click is not None:
                logger.info(f'Table: {repr(table_click)}')
                res = self.__table_click(table_click)
                if not res:
                    nd = self.__systems.layout.root
                    Sequence(PosInterval(nd, 0.05, Vec2(0.01, 0),
                                         blend=BlendType.EASE_IN_OUT),
                             PosInterval(nd, 0.1, Vec2(-0.01, 0),
                                         blend=BlendType.EASE_IN_OUT),
                             PosInterval(nd, 0.05, Vec2(0, 0),
                                         blend=BlendType.EASE_IN_OUT)).play()
                    self.__systems.game_table.invalid_move()
                else:
                    self.__state.fresh_state = False
                self.__update_attempt()
                return

    # Click helper methods

    def __table_click(self, table_click) -> bool:
        """Evaluates possible moves for table clicks."""
        if table_click[0] == common.TableArea.STACK:
            self.__systems.game_table.draw()
            return True
        if table_click[0] == common.TableArea.WASTE:
            if self.config.getboolean(
                    'pyos', 'waste_to_foundation', fallback=False):
                res = self.__systems.game_table.waste_to_foundation()
                if not res:
                    res = self.__systems.game_table.waste_to_tableau()
            else:
                res = self.__systems.game_table.waste_to_tableau()
                if not res:
                    res = self.__systems.game_table.waste_to_foundation()
            return res
        if table_click[0] == common.TableArea.FOUNDATION:
            return self.__systems.game_table \
                    .foundation_to_tableau(table_click[1][0])
        # TABLEAU
        from_pile = self.__systems.game_table.table.tableau[table_click[1][0]]
        num_cards = len(from_pile) - table_click[1][1]
        if num_cards == 1:
            res = self.__systems.game_table.flip(table_click[1][0])
            if res:
                return res
            res = self.__systems.game_table \
                    .tableau_to_foundation(table_click[1][0])
            if res:
                return res
        res = self.__systems.game_table \
                .tableau_to_tableau(from_pile=table_click[1][0],
                                    num_cards=num_cards)
        return res

    # Game State

    def __update_attempt(self, solved=False, bonus=0):
        mvs, tim, pts = self.__systems.game_table.stats
        undo, invalid = self.__systems.game_table.undo_invalid
        self.stats.update_attempt(moves=mvs, duration=tim, points=pts,
                                  undo=undo, invalid=invalid, solved=solved,
                                  bonus=bonus)


    def __save(self):
        path = os.path.join(self.config['base']['cache_dir'],
                            self.config['pyos']['state_file'])
        with open(path, 'wb') as f_handler:
            f_handler.write(self.__systems.game_table.get_state(pause=False))

    def __load(self):
        path = os.path.join(self.config['base']['cache_dir'],
                            self.config['pyos']['state_file'])
        if os.path.isfile(path):
            with open(path, 'rb') as f_handler:
                self.__systems.game_table.set_state(f_handler.read())
            self.__state.refresh_next_frame = 2
        else:
            self.__new_deal()

    def __show_score(self):
        """Show the result screen."""
        self.__save()
        dur, pts, bonus, moves = self.__systems.game_table.result
        mins = int(dur / 60)
        secs = dur - mins * 60
        txt = f'Daily deal WON!' if self.__state.day_deal else f'You WON!'
        txt += '\n\n'
        scr = f'{pts + bonus}'
        top = False
        i = self.stats.highscore(self.__systems.game_table.draw_count)
        logger.debug(f'Current highscore: {i}')
        if pts + bonus > i:
            scr += f' {chr(0xf01b)}'
            top = True
        mvs = f'{moves}'
        i = self.stats.least_moves(self.__systems.game_table.draw_count)
        logger.debug(f'Current least_moves: {i}')
        if moves <= i:
            mvs += f' {chr(0xf01b)}'
            top = True
        tim = f'{mins}:{secs:05.2f}'
        i = self.stats.fastest(self.__systems.game_table.draw_count)
        logger.debug(f'Current fastest: {i}')
        if dur < i:
            tim += f' {chr(0xf01b)}'
            top = True
        mlen = max(len(scr), len(mvs), len(tim))
        txt += f'Score: {" " * (mlen - len(scr))}{scr}\n'
        txt += f'Moves: {" " * (mlen - len(mvs))}{mvs}\n'
        txt += f'Time:  {" " * (mlen - len(tim))}{tim}\n\n'
        if top:
            txt += f'{chr(0xf01b)} Personal best\n'
        txt += '\n\n'
        self.__gen_dlg(txt)
        if not self.__state.fresh_state:
            self.__win_animation()
            self.__update_attempt(solved=True, bonus=bonus)
        self.__disable_all()
        self.__state.day_deal = False

    def __gen_dlg(self, txt: str):
        if self.__systems.windlg is None:
            fnt = self.config.get('font', 'bold')
            buttons = [DialogueButton(text='New Game',
                                      fmtkwargs={'size': (0.35, 0.1),
                                                 'font': fnt,
                                                 'text_color': (0, 50, 0, 255),
                                                 'down_text_color': (255, 255,
                                                                     255, 255),
                                                 'border_thickness': 0.005,
                                                 'down_border_thickness': 0.008,
                                                 'border_color': (0, 50, 0),
                                                 'down_border_color': (255, 255,
                                                                       255),
                                                 'corner_radius': 0.05,
                                                 'multi_sampling': 2,
                                                 'align': 'center'},
                                      callback=self.__new_deal)]
            dlg = Dialogue(text=txt, buttons=buttons, margin=0.01,
                           size=(0.7, 0.7), font=fnt, align='center',
                           frame_color=(40, 120, 20), border_thickness=0.01,
                           corner_radius=0.05, multi_sampling=2)
            dlg.pos = -0.35, -0.35
            dlg.reparent_to(self.ui.center)
            self.__systems.windlg = dlg
        else:
            self.__systems.windlg.text = txt
            self.__systems.windlg.show()

    def __win_animation(self):
        scx, scy = self.screen_size
        caw, cah = self.__systems.layout.card_size
        scx, scy = scx / min(scx, scy) - caw, scy / min(scx, scy) - cah
        blends = [BlendType.EASE_OUT]  + [BlendType.EASE_IN_OUT] * 3
        depth = list(range(52))
        random.shuffle(depth)
        offset = 0
        for suit in range(4):
            for value in range(13):
                nd = self.__systems.layout.get_card((suit, value))
                seqa = []
                seqb = []
                for blend in blends:
                    dur = random.random() * 0.8
                    pos = Vec2(random.random() * scx, random.random() * scy)
                    seqa.append(PosInterval(nd, dur, pos, blend=blend))
                    angle = random.random() * 1440 - 720
                    seqb.append(RotationInterval(nd, dur, angle, blend=blend))
                dur = random.random() * 0.8
                pos = Vec2(offset)
                angle = 0
                offset += 0.0002
                seqa.append(PosInterval(nd, dur, pos,
                                        rel=self.__systems.layout.stack,
                                        blend=blend))
                seqa.append(DepthInterval(nd, 0.5, suit * 13 + value))
                seqb.append(RotationInterval(nd, dur, angle, blend=blend))
                Sequence(*seqa).play()
                Sequence(*seqb).play()
                nd.depth = depth.pop()

    # Interaction

    def __undo_move(self):
        """On Undo click: Undo the last move."""
        if self.__systems.game_table.win_condition:
            return
        res = self.__systems.game_table.undo()
        if res:
            self.__state.last_undo = True
            self.__update_attempt()

    def __reset_deal(self):
        """On Reset click: Reset the current game to start."""
        dlg = self.__systems.windlg
        if dlg is not None and not dlg.hidden:
            dlg.hide()
            self.__setup()
        self.__systems.game_table.reset()
        self.__state.refresh_next_frame = 2
        if self.__state.day_deal:
            self.stats.new_attempt(self.__systems.game_table.seed,
                                   self.__systems.game_table.draw_count,
                                   True, True)
        else:
            self.stats.new_attempt(self.__systems.game_table.seed,
                                   self.__systems.game_table.draw_count,
                                   self.config.getboolean('pyos',
                                                          'winner_deal'))

    def __new_deal(self):
        """On New Deal click: Deal new game."""
        dlg = self.__systems.windlg
        if dlg is not None and not dlg.hidden:
            dlg.hide()
            self.__setup()
        if self.daydeal is not None:
            draw, seed = self.daydeal
            self.__systems.game_table.draw_count = draw
            self.__systems.game_table.deal(seed, win_deal=True)
            self.stats.new_deal(seed, draw, True, True)
            self.stats.new_attempt(seed, draw, True, True)
            self.daydeal = None
            self.__state.day_deal = True
            logger.debug('Started a daydeal')
        elif self.__state.day_deal and self.need_new_game:
            pass
        else:
            if self.config.getboolean('pyos', 'draw_one'):
                self.__systems.game_table.draw_count = 1
            else:
                self.__systems.game_table.draw_count = 3
            win_deal = self.config.getboolean('pyos', 'winner_deal')
            self.__systems.game_table.deal(win_deal=win_deal)
            self.__state.refresh_next_frame = 2
            seed = self.__systems.game_table.seed
            draw = self.__systems.game_table.draw_count
            self.stats.new_deal(seed, draw, win_deal)
            self.stats.new_attempt(seed, draw, win_deal)
            self.__state.day_deal = False
            logger.debug('Started a regular deal')
        self.need_new_game = False

    def __menu(self):
        """On Menu click."""
        self.request('main_menu')
