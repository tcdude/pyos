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

from sdl2.ext import Entity

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'


class Card(object):
    def __init__(
            self,
            value,
            suit,
            visible=False,
            area='s',
            col=None,
            row=None):
        self.value = value
        self.suit = suit
        self.visible = visible
        self.area = area
        self.col = col
        self.row = row
        self.in_anim = False


class CardEntity(Entity):
    def __init__(
            self, world, sprite, value, suit, visible=False, x=0, y=0, d=0):
        self.__world = world
        self.sprite = sprite
        self.sprite.position = x, y
        self.sprite.depth = d
        self.card = Card(value, suit, visible)


class PlaceHolderEntity(Entity):
    def __init__(self, world, sprite, x=0, y=0, d=0):
        self.__world = world
        self.sprite = sprite
        self.sprite.position = x, y
        self.sprite.depth = d
