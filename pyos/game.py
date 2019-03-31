"""
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

import pickle
import os
import logging
from logging.config import dictConfig

import sdl2
from sdl2.ext import Applicator

from common import APPNAME
from common import BOTTOM_BAR
from common import COL_SPACING
from common import CONFIG
from common import CONFIGFILE
from common import FONT_NORMAL
from common import get_scale
from common import get_table
from common import RATIO
from common import get_cards
from common import ROW_SPACING
from common import STATEFILE
from common import TABLEAU_SPACING
from common import TOP_BAR
from component import CardEntity
from component import PlaceHolderEntity
from engine.app import App
from engine.vector import Vector
from table import Table

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.1'


class Game(App):
    def __init__(self):
        super(Game, self).__init__(APPNAME)
        # Config
        self.__config__ = {}
        if os.path.isfile(CONFIGFILE):
            self.__config__.update(pickle.loads(open(CONFIGFILE, 'rb').read()))
        else:
            self.__config__.update(CONFIG)

        # Image Paths
        self.__card_img__ = {}
        self.__cardback_img__ = None

        # Entities
        self.__bg__ = []
        self.__cards__ = {}
        self.__bt_bar__ = []

        # Locations / Size
        self.__cr_sep__ = int(self.screen_size[1] * ROW_SPACING)
        self.__cardsize__ = (0, 0)
        self.__f_pos__ = []
        self.__s_pos__ = (0, 0)
        self.__w_pos__ = (0, 0)
        self.__t_pos__ = []

        # State
        self.__table__ = Table()
        self.__drag__ = False
        self.__invalid_drag__ = False
        self.__d_ent__ = []
        self.__drag_origin__ = None
        self.__orig_depth__ = 0
        self.__last_click__ = 0.0
        self.__m_d_pos__ = Vector()
        self.__last_mouse__ = Vector()
        self.__down__ = False

        # Setup
        self.setup()
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
            self.back
        )
        if self.isandroid:
            self.event_handler.listen(
                'finger_down',
                sdl2.SDL_FINGERDOWN,
                self.mouse_down
            )
            self.event_handler.listen(
                'finger_up',
                sdl2.SDL_FINGERUP,
                self.mouse_up
            )
        else:
            self.event_handler.listen(
                'mouse_down',
                sdl2.SDL_MOUSEBUTTONDOWN,
                self.mouse_down
            )
            self.event_handler.listen(
                'mouse_up',
                sdl2.SDL_MOUSEBUTTONUP,
                self.mouse_up
            )
        self.task_manager.add_task('drag_task', self.drag_task)
        # Logging
        dictConfig({
            'version': 1,
            'disable_existing_loggers': True,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s | %(levelname)s | %(filename)s:'
                              '%(funcName)s:%(lineno)d => %(message)s'
                },
            },
            'handlers': {
                'default': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'standard'
                },
            },
            'loggers': {
                '': {
                    'handlers': ['default'],
                    'level': 'DEBUG',
                    'propagate': True
                }
            }
        })

        self.log.info('pyos started')

    @property
    def log(self):
        return logging

    @property
    def table(self):
        return self.__table__

    # noinspection PyUnusedLocal
    def mouse_down(self, event):
        self.__down__ = True
        if self.isandroid:
            self.__update_mouse__()
        if event.type == sdl2.SDL_TouchFingerEvent:
            self.__m_d_pos__ = Vector(
                int(event.x * (self.screen_size[0] - 1)),
                int(event.y * (self.screen_size[1] - 1))
            )
            self.log.debug('finger down')
        else:
            self.__m_d_pos__ = self.mouse_pos
            self.log.debug(f'mouse button down [{self.mouse_pos}]')

    # noinspection PyUnusedLocal
    def drag_task(self, *args, **kwargs):
        if self.__invalid_drag__:
            return
        if self.__down__ and not self.__drag__:

            dist = (self.mouse_pos - self.__m_d_pos__).length
            if dist > self.__config__['drag_threshold']:
                self.__drag_origin__, self.__d_ent__ = self.get_drag_entities()
                if not self.__d_ent__:
                    self.__invalid_drag__ = True
                    return
                self.__orig_depth__ = self.__d_ent__[0].sprite.depth
                self.__drag__ = True
                self.__last_mouse__ = self.__m_d_pos__
                self.log.debug('start drag')
        if self.__drag__:
            dx, dy = self.mouse_pos - self.__last_mouse__
            self.__last_mouse__ = self.mouse_pos
            for i, e in enumerate(self.__d_ent__):
                x, y = e.sprite.position
                e.sprite.position = x + dx, y + dy
                e.sprite.depth = 100 + i

    def get_drag_entities(self):
        a = self.check_click_pos(self.__m_d_pos__)
        if a in ('s', None):
            return 's', []
        if a == 'w' and len(self.table.waste):
            return 'w', [self.__cards__[self.table.waste[-1]]]
        elif a == 'f':
            for i, f in enumerate(self.table.foundation):
                if not f:
                    continue
                sx = self.__f_pos__[i][0]
                ex = sx + self.__cardsize__[0]
                if sx <= self.__m_d_pos__.x <= ex:
                    return f'f{i}', [self.__cards__[f[-1]]]
        elif a == 't':
            col = self.__m_d_pos__.x / (self.screen_size[0] / 7)
            col = min(6, int(col))
            if not self.table.tableau[col]:
                return f't{col}', []
            row = self.get_tableau_row(col, self.__m_d_pos__)
            if row == -1:
                return f't{col}', [
                    self.__cards__[self.table.tableau[col][-1][0]]
                ]
            else:
                return (
                    f't{col}',
                    [
                        self.__cards__[c[0]]
                        for c in self.table.tableau[col][row:]
                    ]
                )
        return None, None

    # noinspection PyUnusedLocal
    def mouse_up(self, event):
        self.__down__ = False
        sa = self.check_click_pos(self.__m_d_pos__)
        ea = self.check_click_pos()
        if self.__invalid_drag__:
            self.__invalid_drag__ = False
            if not (sa == ea is not None):
                self.__drag__ = False
                return
        process_click = True
        if self.__drag__:
            process_click = self.end_drag(sa, ea)
        if not process_click:
            return
        a = self.check_click_pos()
        if a == 's':
            self.stack_click()
        elif a == 'w':
            self.waste_click()
        elif a == 't':
            self.tableau_click()
        elif a == 'f':
            self.foundation_click()
        elif a == 'b' and self.mouse_pos.x < self.screen_size[0] // 3:
            self.stop_all_position_sequences()
            self.deal()
        if self.table.win_condition:
            self.stop_all_position_sequences()
            t, p, b, m = self.table.result
            self.log.info(f'{t:.1f} Seconds, {p} Points, {b} Bonus, {m} Moves')
            self.deal()

    def end_drag(self, start_area, end_area):
        process_click = True
        if start_area == end_area != 't':
            invalid = True
        else:
            to_foundation = True if end_area == 'f' else False
            if to_foundation and len(self.__d_ent__) > 1:
                self.log.debug('tried to drag multiple cards to foundation')
                invalid = True
            elif end_area in ('w', 's', None):
                self.log.debug(f'tried to drop on invalid area={str(end_area)}')
                invalid = True
            else:
                sti = self.get_array_index('t', self.__m_d_pos__)
                srow = self.get_tableau_row(sti, self.__m_d_pos__)
                eti = self.get_array_index('t', self.mouse_pos)
                sfi = self.get_array_index('f', self.__m_d_pos__)
                efi = self.get_array_index('f', self.mouse_pos)
                if start_area == 'w':
                    if end_area == 't':
                        self.log.debug(f'waste_to_tableau(col={eti})')
                        invalid = not self.table.waste_to_tableau(
                            col=eti
                        )
                        if not invalid:
                            self.update_tableau(eti)
                    elif end_area == 'f':
                        self.log.debug(f'waste_to_foundation(col={efi})')
                        invalid = not self.table.waste_to_foundation(
                            col=efi
                        )
                        if not invalid:
                            self.update_foundation(efi)
                    else:
                        self.log.debug('invalid waste_to_... move')
                        invalid = True
                    if not invalid:
                        self.update_waste()
                elif start_area == 't':
                    if end_area == 't':
                        self.log.debug(
                            f'tableau_to_tableau(scol={sti}, ecol={eti}, srow='
                            f'{srow})'
                        )
                        invalid = not self.table.tableau_to_tableau(
                            scol=sti,
                            ecol=eti,
                            srow=srow
                        )
                        if not invalid:
                            self.update_tableau(eti)
                    elif end_area == 'f':
                        self.log.debug(
                            f'tableau_to_foundation(col={sti}, fcol={efi})'
                        )
                        invalid = not self.table.tableau_to_foundation(
                            col=sti,
                            fcol=efi
                        )
                        if not invalid:
                            self.update_foundation(efi)
                    else:
                        self.log.debug('invalid tableau_to_... move')
                        invalid = True
                    if not invalid:
                        self.update_tableau(sti)
                elif start_area == 'f':
                    if end_area == 't':
                        self.log.debug(
                            f'foundation_to_tableau(col={sfi}, tcol={eti})'
                        )
                        invalid = not self.table.foundation_to_tableau(
                            col=sfi,
                            tcol=eti,
                        )
                        if not invalid:
                            self.update_tableau(eti)
                    else:
                        self.log.debug('invalid foundation_to_... move')
                        invalid = True
                    if not invalid:
                        self.update_foundation(sfi)
                else:
                    self.log.warning(
                        f'unhandled drag event: start_area={str(start_area)}, '
                        f'end_area={str(end_area)}, sti={sti}, srow={srow}, '
                        f'eti={eti}, sfi={sfi}, efi={efi}'
                    )
                    invalid = True
        if invalid:
            self.log.debug('!!invalid move!!')
            dx, dy = self.__m_d_pos__ - self.mouse_pos
            for i, e in enumerate(self.__d_ent__):
                x, y = e.sprite.position
                e.sprite.position = x + dx, y + dy
                e.sprite.depth = self.__orig_depth__ + i
        else:
            self.log.debug('!!valid move!!')
            process_click = False
        self.__drag__ = False
        self.__d_ent__ = []
        return process_click

    def check_click_pos(self, mouse_pos=None):
        """Return a single lowercase letter for the clicked area or None"""
        if mouse_pos is None:
            mouse_pos = self.mouse_pos

        # Stack
        sx = self.__s_pos__[0]
        ex = sx + self.__cardsize__[0]
        sy = self.__s_pos__[1]
        ey = sy + self.__cardsize__[1]
        if sx <= mouse_pos.x <= ex and sy <= mouse_pos.y <= ey:
            return 's'

        # Waste
        sx = self.__w_pos__[0]
        if self.__config__['left_handed']:
            sx += min(len(self.table.waste) - 1, 3) * self.__cr_sep__
        ex = sx + self.__cardsize__[0]
        sy = self.__w_pos__[1]
        ey = sy + self.__cardsize__[1]
        if sx <= mouse_pos.x <= ex and sy <= mouse_pos.y <= ey:
            return 'w'

        # Tableau
        sy = self.__t_pos__[0][1]
        max_pile = max([len(i) - 1 for i in self.table.tableau] + [0])
        ey = sy + max_pile * self.__cr_sep__ + self.__cardsize__[1]
        if sy <= mouse_pos.y <= ey:
            return 't'

        # Foundation
        sx = min(self.__f_pos__[0][0], self.__f_pos__[-1][0])
        ex = max(self.__f_pos__[0][0], self.__f_pos__[-1][0])
        ex += self.__cardsize__[0]
        sy = self.__f_pos__[0][1]
        ey = self.__f_pos__[-1][1] + self.__cardsize__[1]
        if sx <= mouse_pos.x <= ex and sy <= mouse_pos.y <= ey:
            return 'f'

        # Bottom Bar
        sx = 0
        ex = self.screen_size[0]
        sy = self.screen_size[1] - int(self.screen_size[1] * BOTTOM_BAR[1])
        ey = self.screen_size[1]
        if sx <= mouse_pos.x <= ex and sy <= mouse_pos.y <= ey:
            return 'b'
        return None

    def back(self, event):
        """Handles Android Back, Escape and Backspace Events"""
        if event.key.keysym.sym in (
                sdl2.SDLK_AC_BACK, 27, sdl2.SDLK_BACKSPACE):
            with open(STATEFILE, 'wb') as f:
                f.write(self.table.get_state())
            self.quit(blocking=False)

    def setup(self):
        # General
        left_handed = self.__config__['left_handed']
        self.init_font_manager(
            FONT_NORMAL,
            'normal',
            28,
            bg_color=sdl2.ext.Color(85, 85, 85, 0)
        )
        self.__bt_bar__ = []
        sprite = self.text_sprite('| New Deal |')
        self.log.debug(f'{type(sprite)}, {str(sprite)}')
        self.__bt_bar__.append(PlaceHolderEntity(
            self.world,
            sprite,
            int(self.screen_size[0] * (1 - BOTTOM_BAR[0])),
            self.screen_size[1] - int(self.screen_size[1] * BOTTOM_BAR[1] * 0.85)
        ))
        self.__bt_bar__[0].sprite.depth = 100

        # Table
        table = get_table(
            self.screen_size,
            RATIO,
            left_handed
        )
        self.__bg__ = PlaceHolderEntity(self.world, self.load_sprite(table))

        # Positions
        cx, cy = self.__cardsize__ = get_scale(self.screen_size, RATIO)
        col = int(self.screen_size[0] * COL_SPACING)
        y_start = int(self.screen_size[1] * TOP_BAR[1])
        r = range(6, 2, -1) if left_handed else range(4)
        self.__f_pos__ = [(col + i * (cx + col), y_start) for i in r]
        self.__w_pos__ = (col + (1 if left_handed else 5) * (cx + col), y_start)
        self.__s_pos__ = (col + (0 if left_handed else 6) * (cx + col), y_start)
        y_start = y_start + cy + int(self.screen_size[1] * TABLEAU_SPACING)
        self.__t_pos__ = [(col + i * (cx + col), y_start) for i in range(7)]

        # Cards
        cards = get_cards(self.screen_size, RATIO)
        self.__cardback_img__ = cards.pop((-1, -1))
        self.__card_img__.update(cards)
        self.__cards__ = {
            k: CardEntity(
                self.world,
                self.load_sprite(self.__cardback_img__),
                k[1],
                k[0],
                False,
                self.__s_pos__[0],
                self.__s_pos__[1],
                2
            ) for k in self.__card_img__
        }
        if os.path.isfile(STATEFILE):
            with open(STATEFILE, 'rb') as f:
                self.table.set_state(f.read())
            self.update_tableau()
            self.update_foundation()
            self.update_waste()
        else:
            self.deal()

    def deal(self, random_seed=None):
        self.table.deal(random_seed)
        self.update_foundation()
        self.reset_stack()
        self.update_tableau()
        self.update_waste()

    def stack_click(self):
        res = self.table.draw(self.__config__['draw_one'])
        if res == 0:
            self.update_waste()
        elif res == 1:
            self.reset_stack()

    def waste_click(self):
        k = self.table.waste[-1] if self.table.waste else None
        if self.table.waste_to_tableau():
            self.move_card(k, 't')
            self.update_waste()
            return
        if self.table.waste_to_foundation():
            self.move_card(k, 'f')
            self.update_waste()
            return
        if self.table.waste:
            self.anim_shake(self.__cards__[self.table.waste[-1]])

    def tableau_click(self):
        i = self.get_array_index('t', self.mouse_pos)
        row = self.get_tableau_row(i, self.mouse_pos)
        tableau = self.table.tableau[i]
        if not tableau or row is None:
            return
        movable = tableau[row:]
        if row > -1 and tableau[row] != tableau[-1]:
            if tableau[row][0][1] == 12 and tableau[row][1] == 1 and row < 1:
                for k, _ in movable:
                    self.anim_shake(self.__cards__[k])
                return
        if tableau and tableau[row][1] == 0:  # Flip Card
            if row == -1:
                tableau[row][1] = 1
                self.__cards__[tableau[row][0]].card.visible = True
                self.update_tableau(i)
                self.table.increment_moves()
                return
            if not self.__cards__[tableau[row][0]].card.visible:
                return
        if row == -1:
            k = self.table.tableau[i][row][0]
            if self.table.tableau_to_foundation(col=i):
                self.move_card(k, 'f')
                return
            if self.table.tableau_to_tableau(scol=i):
                self.move_card(k, 't')
                return
        if self.table.tableau_to_tableau(scol=i, srow=row):
            self.log.debug(f'row={row} move {str(movable)}')
            for k, _ in movable:
                self.move_card(k, 't')
        else:
            for k, _ in movable:
                if self.__cards__[k].card.visible:
                    self.anim_shake(self.__cards__[k])

    def foundation_click(self):
        i = self.get_array_index('f', self.mouse_pos)
        k = self.table.foundation[i][-1] if len(self.table.foundation[i]) else None
        if self.table.foundation_to_tableau(col=i):
            self.move_card(k, 't')
            # self.update_foundation(i)
            # self.update_tableau()
        else:
            c = self.get_card_under_mouse('f')
            if c is not None:
                self.anim_shake(c)

    def move_card(self, k, area):
        dest = None
        target_depth = 0
        card = self.__cards__[k]
        if area == 't':
            search = [k, 1 if card.card.visible else 0]
            arr = self.table.tableau
        elif area == 'f':
            search = k
            arr = self.table.foundation
        else:
            raise ValueError('expected either "t" or "f" for argument area')

        for i, t in enumerate(arr):
            if search in t:
                row = t.index(search)
                if area == 't':
                    dest = Vector(*self.get_tableau_pos(i, row))
                else:
                    dest = Vector(*self.__f_pos__[i])
                target_depth = row + 2
                break
        if dest is None:
            raise ValueError('cannot find moved card on tableau')
        self.anim_fly_to(
            self.__cards__[k],
            dest,
            target_depth
        )

    def anim_fly_to(self, card, dest, target_depth, speed=None):
        if speed is None:
            speed = 1.0 / (min(self.screen_size) * 3.8)
        start = Vector(*card.sprite.position)
        distance = (dest - start).length
        depth = card.sprite.depth + 40
        self.position_sequence(
            card,
            depth,
            ((distance * speed, start, dest),),
            self.update_card,
            card,
            new_depth=target_depth,
            in_anim=False
        )
        card.card.in_anim = True

    def anim_shake(self, card, duration=0.2, delta_x=0.05, delta_y=0.0):
        x, y = card.sprite.position
        d = duration / 8
        mx = int(self.__cardsize__[0] * delta_x)
        my = int(self.__cardsize__[1] * delta_y)
        od = card.sprite.depth
        self.position_sequence(card, od, (
            (d, Vector(x, y), Vector(x + mx, y + my)),
            (d, Vector(x + mx, y + my), Vector(x, y)),
            (d, Vector(x, y), Vector(x - mx, y - my)),
            (d, Vector(x - mx, y - my), Vector(x, y)),
            (d, Vector(x, y), Vector(x + mx, y + my)),
            (d, Vector(x + mx, y + my), Vector(x, y)),
            (d, Vector(x, y), Vector(x - mx, y - my)),
            (d, Vector(x - mx, y - my), Vector(x, y)),
        ))

    def update_card(
            self,
            card,
            position=None,
            new_depth=None,
            visible=None,
            in_anim=None):
        k = card.card.suit, card.card.value
        if visible is not None:
            if card.card.visible != visible:
                card.card.visible = visible
                if visible:
                    card.sprite = self.load_sprite(self.__card_img__[k])
                else:
                    card.sprite = self.load_sprite(self.__cardback_img__)
        if position is not None:
            card.sprite.position = position
        if new_depth is not None:
            card.sprite.depth = new_depth
        if in_anim is not None:
            card.card.in_anim = in_anim

    def update_tableau(self, col=None):
        for col in range(7) if col is None else [col]:
            x = self.__t_pos__[col][0]
            sy = self.__t_pos__[col][1]
            for row, (k, v) in enumerate(self.table.tableau[col]):
                y = sy + row * self.__cr_sep__
                self.__cards__[k].card.visible = True if v else False
                if self.__cards__[k].card.visible:
                    self.__cards__[k].sprite = self.load_sprite(
                        self.__card_img__[k]
                    )
                else:
                    self.__cards__[k].sprite = self.load_sprite(
                        self.__cardback_img__
                    )
                if not self.__cards__[k].card.in_anim:
                    if self.__cards__[k].sprite.position != (x, y):
                        self.__cards__[k].sprite.position = x, y
                    self.__cards__[k].sprite.depth = 2 + row

    def update_foundation(self, col=None):
        for col in range(4) if col is None else [col]:
            for i, k in enumerate(self.table.foundation[col]):
                if not self.__cards__[k].card.visible:
                    self.__cards__[k].card.visible = True
                    self.__cards__[k].sprite = self.load_sprite(
                        self.__card_img__[k]
                    )
                if not self.__cards__[k].card.in_anim:
                    self.__cards__[k].sprite.position = self.__f_pos__[col]
                    self.__cards__[k].sprite.depth = 2 + i

    def update_waste(self):
        x_rh = self.__w_pos__[0]
        x_lh = x_rh + min(len(self.table.waste) - 1, 3) * self.__cr_sep__
        for i, k in enumerate(reversed(self.table.waste[-4:])):
            card = self.__cards__[k]
            card.sprite = self.load_sprite(self.__card_img__[k])
            x = (x_lh if self.__config__['left_handed'] else x_rh)
            x -= i * self.__cr_sep__
            if not card.card.in_anim:
                card.sprite.position = x, self.__w_pos__[1]
            card.sprite.depth = 6 - i
            card.card.visible = True
        for i in range(len(self.table.waste) - 4):
            self.__cards__[self.table.waste[i]].sprite.depth = 1

    def reset_stack(self):
        for k in self.table.stack:
            self.__cards__[k].sprite = self.load_sprite(self.__cardback_img__)
            self.__cards__[k].sprite.position = (
                self.__s_pos__[0],
                self.__s_pos__[1]
            )
            self.__cards__[k].card.visible = False

    def get_tableau_pos(self, col, row):
        return (
            self.__t_pos__[col][0],
            self.__t_pos__[col][1] + self.__cr_sep__ * row
        )

    def get_array_index(self, area, mouse_pos=None):
        if mouse_pos is None:
            mouse_pos = self.mouse_pos
        if area == 'f':
            for i, _ in enumerate(self.table.foundation):
                sx = self.__f_pos__[i][0]
                ex = sx + self.__cardsize__[0]
                if sx <= mouse_pos.x <= ex:
                    return i
        elif area == 't':
            col = mouse_pos.x / (self.screen_size[0] / 7)
            col = min(6, int(col))
            return col
        return -1

    def get_tableau_row(self, col, mouse_pos=None):
        if mouse_pos is None:
            mouse_pos = self.mouse_pos
        sy = self.__t_pos__[col][1]
        ey = sy + self.__cardsize__[1]
        ey += len(self.table.tableau[col]) * self.__cr_sep__
        if sy <= mouse_pos.y <= ey:
            if mouse_pos.y >= ey - self.__cardsize__[1]:
                return -1
            return int((mouse_pos.y - sy) / self.__cr_sep__)
        return None

    def get_card_under_mouse(self, area=None):
        if area is None:
            area = self.check_click_pos()
        if area == 'f':
            i = self.get_array_index(area)
            if i != -1:
                f = self.table.foundation[i]
                return self.__cards__[f[-1]] if len(f) else None
        elif area == 't':
            col = self.get_array_index(area)
            if len(self.table.tableau[col]):
                return self.__cards__[self.table.tableau[col][-1][0]]
        elif area == 'w':
            return self.__cards__[self.table.waste[-1]]
        return None


class GameApplicator(Applicator):
    """
    Applicator to handle all Game Components.
    """
    def __init__(self):
        super(GameApplicator, self).__init__()
        self.componenttypes = ()

    def process(self, world, components):
        pass

    def enter(self):
        pass

    def exit(self):
        pass


class MenuApplicator(Applicator):
    """
    Applicator to handle all Menu/GUI Components.
    """
    def __init__(self):
        super(MenuApplicator, self).__init__()
        self.componenttypes = ()

    def process(self, world, components):
        pass

    def enter(self):
        pass

    def exit(self):
        pass
