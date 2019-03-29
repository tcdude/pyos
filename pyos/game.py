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
from math import ceil
import os

import sdl2
from sdl2.ext import Applicator

from common import APPNAME
from common import ASSETDIR
from common import BACKGROUND
from common import COL_SPACING
from common import CONFIG
from common import CONFIGFILE
from common import get_empty
from common import get_scale
from common import get_table
from common import RATIO
from common import get_cards
from common import TABLEAU_SPACING
from common import TOP_BAR
from component import CardEntity
from component import PlaceHolderEntity
from engine.app import App
from rules import deal
from rules import shuffled_deck

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
        self.__table__ = []
        self.__cards__ = {}
        self.__tableau__ = [[] * 7]
        self.__foundation__ = [[] * 4]
        self.__stack__ = []
        self.__waste__ = []

        # Locations
        self.__f_pos__ = []
        self.__s_pos__ = (0, 0)
        self.__w_pos__ = (0, 0)
        self.__t_pos__ = []

        # State
        self.__drag__ = False
        self.__current_seed__ = None
        self.__deck__ = []

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

    def back(self, event):
        """Handles Android Back, Escape and Backspace Events"""
        if event.key.keysym.sym in (
                sdl2.SDLK_AC_BACK, 27, sdl2.SDLK_BACKSPACE):
            self.quit(blocking=False)

    def setup(self):
        left_handed = self.__config__['left_handed']

        # Table
        table = get_table(
            self.screen_size,
            RATIO,
            left_handed
        )
        self.__bg__ = PlaceHolderEntity(self.world, self.load_sprite(table))

        # Positions
        cx, cy = get_scale(self.screen_size, RATIO)
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
        self.deal()

    def deal(self, random_seed=None):
        self.__current_seed__, self.__tableau__, self.__stack__ = deal(random_seed)
        y_sep = int(self.screen_size[1] * TABLEAU_SPACING)
        for x, pile in enumerate(self.__tableau__):
            x_pos = self.__t_pos__[x][0]
            y_start = self.__t_pos__[x][1]
            for y, (k, o) in enumerate(pile):
                card = self.__cards__[k]
                if o:
                    card.sprite = self.load_sprite(self.__card_img__[k])
                    card.card.visible = True
                else:
                    card.sprite = self.load_sprite(self.__cardback_img__)
                    card.card.visible = False
                card.sprite.position = x_pos, y_start + y * y_sep
                card.sprite.depth = y + 1


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
