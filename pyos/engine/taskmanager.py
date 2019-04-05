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

import time

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'


class Task(object):
    """
    Enables control over
    """
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
        self.__last_exec__ = time.perf_counter()
        self.__active__ = True
        self.__paused__ = False

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

    @property
    def ispaused(self):
        return self.__paused__

    @property
    def isenabled(self):
        return self.__active__

    def pause(self):
        """Pauses current task."""
        self.__paused__ = True

    def resume(self, instant=True):
        """Resumes execution of current task."""
        self.__last_exec__ = time.perf_counter()
        if instant:
            self.__last_exec__ -= self.delay
        self.__paused__ = False

    def disable(self):
        """
        This should only be called by the TaskManager! Prevents further
        execution of the Task.
        """
        self.__active__ = False

    def __call__(self, clk):
        """Execute if enabled and not paused."""
        if not self.__active__ or self.__paused__:
            return
        if self.__last_exec__ + self.delay <= clk:
            dt = clk - self.__last_exec__
            self.__last_exec__ = clk
            kw = {}
            kw.update(self.__kwargs__)
            kw['dt'] = dt
            self.__callback__(*self.__args__, **kw)


class TaskManager(object):
    """
    Rudimentary TaskManager to handle execution of
    """
    def __init__(self):
        self.__tasks__ = {}

    def add_task(self, name, callback, delay=0, *args, **kwargs):
        """
        Return a Task object.

        :str name: unique name of the task
        :callable callback: method to call, must either have **kwargs or accept
                            an argument called `dt`
        :float delay: number of seconds between execution (default=0). This
                      argument must be explicitly passed to `add_task` if
                      optional `args` and/or `kwargs` for `callback` will be
                      passed as well.
        :tuple args: optional positional arguments to be passed to `callback`
        :dict kwargs: optional keyword arguments to be passed to `callback`
        """
        if name in self.__tasks__:
            raise ValueError(f'A Task with the name "{name}" already exists.')
        self.__tasks__[name] = Task(name, callback, delay, args, kwargs)
        return self.__tasks__[name]

    def remove_task(self, name):
        """Remove Task `name` from the TaskManager."""
        if name in self.__tasks__:
            self.__tasks__.pop(name).disable()

    def __call__(self, clk=None):
        # if clk is None:
        clk = time.perf_counter()
        for task in self.__tasks__.values():
            task(clk)

    def __getitem__(self, item):
        if item in self.__tasks__:
            return self.__tasks__[item]
        raise IndexError(f'No task named "{item}"')
