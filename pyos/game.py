"""
Ad free simple Solitaire implementation.
"""

from dataclasses import dataclass
import os
import random
import traceback
from typing import Callable, Tuple, Union

from loguru import logger
import sdl2
from foolysh.animation import DepthInterval, BlendType, PosInterval, Sequence \
                              , RotationInterval
from foolysh.scene.node import Origin
from foolysh.tools.vec2 import Vec2
from foolysh.ui.dialogue import Dialogue, DialogueButton

import app
import common
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
__version__ = '0.3'


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
    suredlg: Union[None, Dialogue] = None


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
    first_move: bool = False
    day_deal: bool = True
    gametype: int = None
    # Need to hold the previous moves or duration for challenges for proper
    # HUD totalization.
    prev_value: Union[int, float] = 0


class Game(app.AppBase):
    """
    Game State.
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
        logger.info('Enter state game')
        self.disable_connection_check()
        self.global_nodes.mpstatus.hide()
        self.global_nodes.hide_status()
        self.__setup()
        if self.global_nodes.seed is None:
            self.__systems.layout.seed.reparent_to(self.ui.bottom_center)
            self.global_nodes.seed = self.__systems.layout.seed \
                .attach_text_node(text='', font_size=0.04,
                                  font=self.config.get('font', 'bold'),
                                  text_color=common.TITLE_TXT_COLOR)
        self.global_nodes.seed.show()
        self.__state.fresh_state = True
        if self.state.challenge > 0:
            self.global_nodes.seed.hide()
            seed, draw, score = self.mps.dbh \
                .get_round_info(self.state.challenge)
            res = self.systems.stats.current_attempt
            if res is not None and res[0].challenge == self.state.challenge \
                  and res[0].seed == seed and res[0].draw == draw \
                  and res[1].solved:
                self.state.challenge = -1
                self.__state.fresh_state = True
                chg = False
            else:
                logger.debug(f'Playing a round in challenge '
                             f'{self.state.challenge}')
                self.__new_deal(seed, draw, score)
                chg = True
        else:
            chg = False
        if self.state.daydeal is None:
            self.__state.day_deal = False
        else:
            self.__state.day_deal = True
        if not chg and (self.state.need_new_game
                        or self.systems.stats.first_launch
                        or self.__state.day_deal
                        or ('unsolved' in self.fsm_global_data
                            and self.fsm_global_data['unsolved'] is not None)):
            self.__new_deal()
        nng = self.__systems.game_table.stats[0] == 0
        nng = nng or self.__systems.game_table.win_condition
        if self.__state.fresh_state:
            self.__state.first_move = True
        if not chg:
            self.__systems.hud.set_gametype()
        self.__systems.toolbar.toggle(not chg)
        self.__systems.toolbar.toggle_order(
            self.config.getboolean('pyos', 'left_handed', fallback=False))
        self.global_nodes.set_seed(self.__systems.game_table.seed)
        common.lock_gamestate()
        logger.debug(f'{repr(self.__state)}')

    def exit_game(self):
        """Tasks to be performed when this state is left."""
        logger.info('Exit state game')
        self.systems.stats.commit_attempt()
        self.fsm_global_data['unsolved'] = None
        self.enable_connection_check()
        common.release_gamestate()
        self.__disable_all()
        self.__hide_dlg()
        self.__systems.layout.root.hide()
        self.__systems.toolbar.hide()
        self.__systems.game_table.pause()
        self.__save()
        self.global_nodes.seed.hide()
        self.global_nodes.mpstatus.show()

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
        logger.debug('Setup complete')
        self.__active = True

    def __setup_events_tasks(self):
        """Setup Events and Tasks."""
        logger.debug('Setup events and tasks')
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
        self.task_manager.add_task('auto_save', self.__auto_save_task, 1, False)
        self.task_manager.add_task('auto_complete', self.__auto_complete,
                                   0.05)
        self.task_manager.add_task('layout_process',
                                   self.__systems.layout.process, 0)

    def __setup_layout(self):
        """One time setup of the scene."""
        if not self.__need_setup:
            return
        logger.debug('Setup layout')
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
                           self.__menu, self.__giveup))
        game_table = Table(layout.callback, self.systems.shuffler)
        layout.set_table(game_table)
        self.__systems = GameSystems(game_table, layout, hud, toolbar)
        self.__need_setup = False

    # Tasks / Events

    def __auto_save_task(self):
        """Auto save task."""
        if not self.global_nodes.mpstatus.hidden:
            self.global_nodes.hide_status()
            self.global_nodes.mpstatus.hide()
        if not self.__systems.game_table.is_paused:
            logger.debug('Auto Save')
            self.__save()
            if self.state.challenge != -1:
                self.__update_attempt(duration_only=True)

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
            meths = ((self.__foundation_move, tbl.tableau_to_foundation),
                     (self.__foundation_move, tbl.waste_to_foundation),
                     (tbl.waste_to_tableau, None), (tbl.draw, None))
        else:
            meths = ((self.__foundation_move, tbl.tableau_to_foundation),
                     (tbl.waste_to_tableau, None),
                     (self.__foundation_move, tbl.waste_to_foundation),
                     (tbl.draw, None))
        for meth, arg in meths:
            if arg is None and meth() or meth(arg):
                self.__state.last_auto = call_time
                self.__update_attempt()
                return
        raise RuntimeError('Unhandled exception.')

    def __update_hud(self, dt):
        """Update HUD."""
        # pylint: disable=invalid-name,unused-argument
        if self.window.size != self.__state.last_window_size \
              or self.state.layout_refresh:
            self.__state.last_window_size = self.window.size
            self.__systems.layout.setup(self.__state.last_window_size,
                                        self.config.getboolean('pyos',
                                                               'left_handed'),
                                        self.config.getboolean('pyos',
                                                               'readability'))
            self.global_nodes.seed.origin = self.__systems.layout.seed.origin
            if self.__systems.layout.seed.origin == Origin.BOTTOM_RIGHT:
                self.__systems.layout.seed.reparent_to(self.ui.bottom_right)
            else:
                self.__systems.layout.seed.reparent_to(self.ui.bottom_center)
            self.__state.refresh_next_frame = 2
            self.state.layout_refresh = False
        elif self.__state.refresh_next_frame > 0:
            self.__state.refresh_next_frame -= 1
            self.__systems.game_table.refresh_table()
            logger.debug('refresh_table')
        moves, elapsed_time, points = self.__systems.game_table.stats
        moves += self.__state.prev_value
        elapsed_time += self.__state.prev_value
        self.__systems.hud.update(points, int(elapsed_time + 0.5), moves)
        if self.__systems.game_table.win_condition:
            self.__systems.layout.setup(self.__state.last_window_size,
                                        self.config.getboolean('pyos',
                                                               'left_handed'),
                                        self.config.getboolean('pyos',
                                                               'readability'))
            self.global_nodes.seed.origin = self.__systems.layout.seed.origin
            self.__systems.layout.process(self.clock.get_dt())
            self.__systems.game_table.refresh_table()
            self.__state.refresh_next_frame = 2
            self.__systems.game_table.pause()
            self.__show_score()
        self.global_nodes.seed.y = -self.global_nodes.seed.size[1]

    def __drag_cb(self, k) -> bool:
        """Callback on start drag of a card."""
        table_click = self.__systems.layout.click_area(self.mouse_pos)
        if table_click is None or table_click[0] == common.TableArea.STACK or \
              self.__systems.layout.get_card(k).index == 1:
            return False
        dragi = self.__state.drag_info
        tbl = self.__systems.game_table.table
        dragi.start_area = table_click[0]
        try:
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
            elif table_click[0] == common.TableArea.WASTE and tbl.waste:
                dragi.pile_id = -1
                dragi.num_cards = 1
                self.__systems.layout.on_drag(tbl.waste[-1].index[0])
            else:  # Unknown
                logger.warning(f'Unable to determine proper drag action for: '
                               f'{table_click}')
                return False
        except IndexError:
            logger.error(f'IndexError in drag callback\n'
                         f'{traceback.format_exc()}')
            return False
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
                    if self \
                          .__foundation_move(self.__systems.game_table \
                              .waste_to_foundation, i):
                        return True
                elif self.__state.drag_info.start_area == common.TableArea \
                      .TABLEAU:
                    if self.__foundation_move(self.__systems.game_table \
                                              .tableau_to_foundation,
                                              self.__state.drag_info.pile_id,
                                              i):
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

        table_click = self.__systems.layout.click_area(self.mouse_pos)
        if table_click is not None:
            logger.debug(f'Table: {repr(table_click)}')
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

    # Click helper methods

    def __table_click(self, table_click) -> bool:
        """Evaluates possible moves for table clicks."""
        tap_move = self.config.getboolean('pyos', 'tap_move')
        if table_click[0] == common.TableArea.STACK:
            self.__systems.game_table.draw()
            return True
        if table_click[0] == common.TableArea.WASTE and tap_move:
            if self.config.getboolean(
                    'pyos', 'waste_to_foundation', fallback=False):
                res = self.__foundation_move(self.__systems.game_table \
                                             .waste_to_foundation)
                if not res:
                    res = self.__systems.game_table.waste_to_tableau()
            else:
                res = self.__systems.game_table.waste_to_tableau()
                if not res:
                    res = self.__foundation_move(self.__systems.game_table \
                                                 .waste_to_foundation)
            return res
        if table_click[0] == common.TableArea.FOUNDATION and tap_move:
            return self.__systems.game_table \
                    .foundation_to_tableau(table_click[1][0])
        # TABLEAU
        from_pile = self.__systems.game_table.table.tableau[table_click[1][0]]
        num_cards = len(from_pile) - table_click[1][1]
        if num_cards == 1:
            res = self.__systems.game_table \
                .flip(table_click[1][0]) or not tap_move
            if res:
                logger.info('Flip tableau card')
                return res
            res = self.__foundation_move(self.__systems.game_table \
                                         .tableau_to_foundation,
                                         table_click[1][0])
            if res:
                return res
        res = self.__systems.game_table \
                .tableau_to_tableau(from_pile=table_click[1][0],
                                    num_cards=num_cards)
        return res

    # Game State

    def __update_attempt(self, solved=False, bonus=0, duration_only=False):
        if self.__systems.game_table.is_paused and not solved:
            return
        logger.debug(f'foundation_moves={self.state.foundation_moves}')
        mvs, tim, pts = self.__systems.game_table.stats
        undo, invalid = self.__systems.game_table.undo_invalid
        logger.debug(f'{repr(self.__state)}')
        if self.__state.first_move and not duration_only and mvs == 1:
            self.__state.first_move = False
            seed = self.__systems.game_table.seed
            draw = self.__systems.game_table.draw_count
            self.systems.stats.new_attempt(seed, draw, True,
                                           self.__state.day_deal,
                                           self.state.challenge)
        self.systems.stats.update_attempt(moves=mvs, duration=tim, points=pts,
                                          undo=undo, invalid=invalid,
                                          solved=solved, bonus=bonus,
                                          write=solved)


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

    def __show_score(self):
        """Show the result screen."""
        self.__save()
        self.systems.stats.update_seed(self.__systems.game_table.draw_count,
                                       self.__systems.game_table.seed,
                                       keep=False)
        if self.state.challenge > -1 and not self.__state.fresh_state:
            pts = self.__systems.game_table.result
            pts = pts[1]
            if self.state.foundation_moves > 55:
                ded = (self.state.foundation_moves - 55) * 20
                logger.warning(f'Deducting points: foundation_moves='
                               f'{self.state.foundation_moves} -> '
                               f'{pts} - {ded}')
                pts = max(0, pts - ded)
                self.systems.stats \
                    .modify_result_points(self.__systems.game_table.seed,
                                          self.__systems.game_table.draw_count,
                                          self.state.challenge, pts)
            self.__update_attempt(solved=True)
            self.state.foundation_moves = 0
            try:
                dur, moves, unused_pts, _ = self.systems \
                    .stats.result(self.__systems.game_table.seed,
                                  self.__systems.game_table.draw_count, True,
                                  False, self.state.challenge)
            except ValueError:
                raise RuntimeError('Win state but no solved result')
            self.fsm_global_data['result'] = dur, moves, pts
            self.request('challenges')
            return
        dur, pts, bonus, moves = self.__systems.game_table.result
        if self.__state.day_deal and not self.__state.fresh_state:
            self.__update_attempt(solved=True, bonus=bonus)
            daydeal = (self.__systems.game_table.draw_count,
                       self.__systems.game_table.seed)
            self.fsm_global_data['daydeal'] = daydeal
            self.__state.day_deal = False
            self.state.daydeal = None
            self.request('day_deal')
            return
        mins, secs = int(dur // 60), dur % 60
        txt = 'You WON!\n\n'
        scr = f'{pts + bonus}'
        top = False
        i = self.systems.stats.highscore(self.__systems.game_table.draw_count)
        logger.debug(f'Current highscore: {i}')
        if pts + bonus > i:
            scr += f' {chr(0xf01b)}'
            top = True
        mvs = f'{moves}'
        i = self.systems.stats.least_moves(self.__systems.game_table.draw_count)
        logger.debug(f'Current least_moves: {i}')
        if moves <= i:
            mvs += f' {chr(0xf01b)}'
            top = True
        tim = f'{mins}:{secs:05.2f}'
        i = self.systems.stats.fastest(self.__systems.game_table.draw_count)
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
        self.fsm_global_data['unsolved'] = None
        if not self.__state.fresh_state:
            self.__win_animation()
            self.__update_attempt(solved=True, bonus=bonus)
        self.__disable_all()

    def __gen_dlg(self, txt: str, dlgtype: str = 'newgame'):
        dlgkw = common.get_dialogue_btn_kw()
        if dlgtype == 'newgame':
            if self.__systems.windlg is None:
                fnt = self.config.get('font', 'bold')
                buttons = [DialogueButton(text='New Game', fmtkwargs=dlgkw,
                                          callback=self.__new_deal)]
                dlg = Dialogue(text=txt, buttons=buttons, margin=0.01,
                               size=(0.7, 0.7), font=fnt, align='center',
                               frame_color=common.FRAME_COLOR_STD,
                               border_thickness=0.01, parent=self.ui.center,
                               corner_radius=0.05, multi_sampling=2)
                dlg.pos = -0.35, -0.35
                self.__systems.windlg = dlg
            else:
                self.__systems.windlg.text = txt
                self.__systems.windlg.show()
        elif dlgtype == 'sure':
            if self.__systems.suredlg is None:
                fnt = self.config.get('font', 'bold')
                dlgkw['size'] = 0.2, 0.1
                buttons = [DialogueButton(text='Yes', fmtkwargs=dlgkw,
                                          callback=self.__giveupdo),
                           DialogueButton(text='No', fmtkwargs=dlgkw,
                                          callback=self.__hide_dlg)]
                dlg = Dialogue(text=txt, buttons=buttons, margin=0.01,
                               size=(0.7, 0.7), font=fnt, align='center',
                               frame_color=common.FRAME_COLOR_STD,
                               border_thickness=0.01, parent=self.ui.center,
                               corner_radius=0.05, multi_sampling=2)
                dlg.pos = -0.35, -0.35
                self.__systems.suredlg = dlg
            else:
                self.__systems.suredlg.text = txt
                self.__systems.suredlg.show()

    def __win_animation(self):
        # pylint: disable=too-many-locals
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
                seqa.append(DepthInterval(nd, 0.001, suit * 13 + value))
                seqa.append(PosInterval(nd, dur, pos,
                                        rel=self.__systems.layout.stack,
                                        blend=blend))
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
        self.state.foundation_moves = 0
        self.__update_prev_value(self.__state.gametype)
        self.__state.refresh_next_frame = 2
        self.__state.first_move = True

    def __new_deal(self, seed: int = None, draw: int = None, score: int = None):
        """On New Deal click: Deal new game."""
        dlg = self.__systems.windlg
        if dlg is not None and not dlg.hidden:
            dlg.hide()
            self.__setup()
        logger.debug(f'New deal called with {seed=} {draw=} {score=}')
        self.__state.gametype = score
        self.__systems.hud.set_gametype(score)
        if seed is not None:
            if self.__systems.game_table.seed != seed \
                  or self.__systems.game_table.draw_count != draw \
                  or self.__systems.game_table.stats[0] <= 0:
                self.__systems.game_table.draw_count = draw
                self.__systems.game_table.deal(seed)
                self.systems.stats.new_deal(seed, draw, True, False,
                                            self.state.challenge)
                self.state.daydeal = None
                self.__state.day_deal = False
                self.state.daydeal = None
                self.__state.first_move = True
                self.state.foundation_moves = 0
            self.__update_prev_value(score)
            self.__systems.toolbar.toggle(False)
            self.__state.fresh_state = False
            logger.debug('Started a challenge round')
        elif self.state.daydeal is not None:
            draw, seed = self.state.daydeal
            if self.__systems.game_table.seed != seed \
                  or self.__systems.game_table.draw_count != draw \
                  or self.__systems.game_table.stats[0] <= 0:
                self.__systems.game_table.draw_count = draw
                self.__systems.game_table.deal(seed)
                self.systems.stats.new_deal(seed, draw, True, True)
                self.__state.first_move = True
            self.__state.day_deal = True
            self.__systems.toolbar.toggle(True)
            self.__state.fresh_state = False
            logger.debug('Started a daydeal')
        elif 'unsolved' in self.fsm_global_data \
              and self.fsm_global_data['unsolved'] is not None:
            seed, draw, daydeal = self.fsm_global_data['unsolved']
            if self.__systems.game_table.seed != seed \
                  or self.__systems.game_table.draw_count != draw \
                  or self.__systems.game_table.stats[0] <= 0:
                self.__systems.game_table.draw_count = draw
                self.__systems.game_table.deal(seed)
                self.systems.stats.new_deal(seed, draw, True, daydeal)
                self.__state.first_move = True
            self.__systems.toolbar.toggle(True)
            self.__state.fresh_state = False
            logger.debug('Started an unsolved deal')
        elif (self.__state.day_deal or self.state.challenge != -1) \
              and self.state.need_new_game:
            pass
        else:
            if self.config.getboolean('pyos', 'draw_one'):
                self.__systems.game_table.draw_count = 1
            else:
                self.__systems.game_table.draw_count = 3
            self.__systems.game_table.deal()
            seed = self.__systems.game_table.seed
            draw = self.__systems.game_table.draw_count
            self.systems.stats.new_deal(seed, draw, True)
            self.__state.day_deal = False
            self.state.daydeal = None
            self.__systems.toolbar.toggle(True)
            self.__state.fresh_state = False
            self.__state.first_move = True
            logger.debug('Started a regular deal')
        self.__state.refresh_next_frame = 2
        self.state.need_new_game = False
        self.global_nodes.set_seed(self.__systems.game_table.seed)

    def __update_prev_value(self, gametype: int):
        """Update the previous attempt total depending on the game type."""
        if gametype == 2 or gametype is None:
            self.__state.prev_value = 0
            return
        count_current = True
        if sum(self.__systems.game_table.stats):
            count_current = False
        self.__state.prev_value = self.systems.stats \
            .attempt_total(self.__systems.game_table.seed,
                           self.__systems.game_table.draw_count,
                           self.state.challenge, gametype, count_current)

    def __menu(self):
        """On Menu click."""
        self.request('main_menu')

    def __giveup(self):
        """On Give Up click."""
        self.__systems.game_table.pause()
        self.__disable_all()
        self.__gen_dlg('Do you really\nwant to give up?\n\n\n', 'sure')

    def __giveupdo(self):
        """Give Up."""
        self.fsm_global_data['result'] = -2.0, 0, 0
        self.request('challenges')

    def __hide_dlg(self):
        """Hide all open dialogues."""
        for dlg in (self.__systems.windlg, self.__systems.suredlg):
            if dlg is not None and not dlg.hidden:
                dlg.hide()

    # Anti Cheat measures
    def __foundation_move(self, meth: Callable, *args) -> bool:
        res = meth(*args)
        if self.state.challenge > -1 and res:
            self.state.foundation_moves += 1
        return res
