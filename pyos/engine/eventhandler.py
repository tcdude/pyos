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

import sdl2.ext

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.1'


class EventHandler(object):
    """
    Basic EventHandler to coordinate SDL2 Events.
    """
    def __init__(self):
        self.__events__ = {}
        self.__unique__ = {}

    def listen(self, name, sdl_event, callback, priority=0, *args, **kwargs):
        """
        Adds a callback to be executed at every call of the EventHandler.

        :str name: Unique name of the event
        :int sdl_event: SDL event type tested against `sdl2.ext.get_events()`
        :callable callback: Method to execute. Must provide `event` as named
                            argument.
        :int priority: Call priority, higher numbers get executed first
                       (default=0).
        :tuple args: optional positional arguments to pass to `callback`
        :dict kwargs: optional keyword arguments to pass to `callback`
        """
        if name in self.__unique__:
            raise ValueError('An event with this name already exists.')
        if sdl_event not in self.__events__:
            self.__events__[sdl_event] = {name: priority}
        self.__unique__[name] = (callback, args, kwargs)

    def forget(self, name):
        """Removes event `name` from the EventHandler"""
        for e in self.__events__:
            if name in self.__events__[e]:
                self.__events__[e].pop(name)
        if name in self.__unique__:
            self.__unique__.pop(name)

    def __call__(self, *args, **kwargs):
        for event in sdl2.ext.get_events():
            if event.type in self.__events__:
                k = reversed(sorted(
                    self.__events__[event.type],
                    key=lambda x: self.__events__[event.type][x]
                ))
                for n in k:
                    c, a, kw = self.__unique__[n]
                    kw['event'] = event
                    c(*a, **kw)
