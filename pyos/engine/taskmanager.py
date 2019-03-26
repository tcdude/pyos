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

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.1'

import time
from queue import Queue


class Task(object):
    def __init__(self, name, callback, delay, args, kwargs):
        if not isinstance(name, str):
            raise ValueError('Argument name must be of type str')
        if not callable(callback):
            raise ValueError('Argument callback must be of type callable')
        if not isinstance(delay, (int, float)) or delay < 0:
            raise ValueError('Expected positive int/float for Argument delay')
        self.__task_name__ = name
        self.__callback__ = callback
        self.__delay__ = delay
        self.__args__ = args
        self.__kwargs__ = kwargs
        self.__last_exec__ = time.clock()
        self.__active__ = True

    @property
    def delay(self):
        return self.__delay__

    @delay.setter
    def delay(self, v):
        if isinstance(v, (int, float)):
            self.__delay__ = v

    @property
    def name(self):
        return self.__task_name__

    def disable(self):
        self.__active__ = False

    def __call__(self, clk):
        if not self.__active__:
            return
        if self.__last_exec__ + self.delay >= clk:
            self.__last_exec__ = clk
            self.__callback__(*self.__args__, **self.__kwargs__)


class TaskManager(object):
    def __init__(self):
        self.__tasks__ = {}
        self.__queue__ = Queue()

    def add_task(self, name, callback, delay=0, *args, **kwargs):
        """
        Returns a Task object.

        :str name: unique name of the task
        :callable callback: method to call
        :float delay: number of seconds between execution
        :tuple args: optional positional arguments to be passed to `callback`
        :dict kwargs: optional keyword arguments to be passed to `callback`
        """
        if name in self.__tasks__:
            raise ValueError(f'A Task with the name "{name}" already exists.')
        self.__tasks__[name] = Task(name, callback, delay, args, kwargs)
        return self.__tasks__[name]

    def remove_task(self, name):
        if name in self.__tasks__:
            self.__tasks__.pop(name).disable()

    def __call__(self, clk=None):
        if clk is None:
            clk = time.clock()
        for t in self.__tasks__.values():
            t(clk)

    def __getitem__(self, item):
        if item in self.__tasks__:
            return self.__tasks__[item]
        raise IndexError(f'No task named "{item}"')
