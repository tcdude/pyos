"""
Provides a simplistic Task Manager to execute either every frame or in a
specified interval.
"""

import time

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


class Task(object):
    """
    Represents a Task that handles execution of the `callback`.

    :param name: The name of the Task
    :param callback: The callable to be called upon execution.
    :param delay: The delay between execution.
    :param args: A Tuple of positional arguments to be passed to `callback`.
    :param kwargs: A Dict of keyword arguments to be passed to `callback`.

    .. note::
        Instantiate through ``task = TaskManager.add_task(...)``

        or access it through indexing ``task = TaskManager['task_name']``.
    """
    def __init__(self, name, callback, delay, with_dt, args, kwargs):
        if not isinstance(name, str):
            raise ValueError('Argument name must be of type str')
        if not callable(callback):
            raise ValueError('Argument callback must be of type callable')
        if not isinstance(delay, (int, float)) or delay < 0:
            raise ValueError('Expected positive int/float for Argument delay')
        self._task_name = name
        self._callback = callback
        self._delay = delay
        self._with_dt = with_dt
        self._args = args
        self._kwargs = kwargs
        self._last_exec = time.perf_counter()
        self._active = True
        self._paused = False

    @property
    def delay(self):
        # type: () -> float
        """``float``"""
        return self._delay

    @delay.setter
    def delay(self, v):
        if isinstance(v, (int, float)):
            self._delay = v

    @property
    def name(self):
        # type: () -> str
        """``str``"""
        return self._task_name

    @property
    def ispaused(self):
        # type: () -> bool
        """``bool``"""
        return self._paused

    @property
    def isenabled(self):
        # type: () -> bool
        """``bool``"""
        return self._active

    def pause(self):
        """Pauses the ``Task``."""
        self._paused = True

    def resume(self, instant=True):
        """
        Resumes execution of the ``Task``.

        :param instant: Optional ``bool`` -> whether to execute the ``Task``
            immediately upon resume or wait for delay (default= ``True`` )
        """
        self._last_exec = time.perf_counter()
        if instant:
            self._last_exec -= self.delay
        self._paused = False

    def disable(self):
        """
        .. note::
            This should only be called by the TaskManager! Prevents further
            execution of the Task.
        """
        self._active = False

    def __call__(self, clk):
        """Execute if enabled and not paused."""
        if not self._active or self._paused:
            return
        if self._last_exec + self.delay <= clk:
            dt = clk - self._last_exec
            self._last_exec = clk
            kw = {}
            kw.update(self._kwargs)
            if self._with_dt:
                kw['dt'] = dt
            self._callback(*self._args, **kw)

    def __repr__(self):
        return f'Task({self.name}, {self.delay:.4f})'

    def __str__(self):
        return self.__repr__()


class TaskManager(object):
    # noinspection PyUnresolvedReferences
    """
        Simplistic Task Manager to handle execution of tasks with given delay.

        Example Usage:

        >>> t = TaskManager()
        >>> task = t.add_task('print_task', print, 0, False, 'hello', 'there')
        >>> t()
        hello there
        >>> t['print_task']
        Task(print_task, 0.0000)

        """
    def __init__(self):
        self._tasks = {}

    def add_task(self, name, callback, delay=0, with_dt=True, *args, **kwargs):
        """
        Return a ``Task`` object.

        :param name: ``str`` -> unique name of the task.
        :param callback: ``callable`` -> method to call, must either have **kwargs
            or accept an argument called ``dt``.
        :param delay: Optional ``int``/``float`` -> number of seconds between
            execution (default=0). This argument must be explicitly passed to
            ``add_task()`` if optional ``args`` and/or ``kwargs`` for
            ``callback`` will be passed as well.
        :param with_dt: Optional ``bool`` -> whether the ``dt`` keyword argument
            will be passed to ``callback`` upon execution.
        :param args: Optional ``tuple`` -> positional arguments to be passed to
            ``callback``.
        :param kwargs: Optional ``dict`` -> keyword arguments to be passed to
            ``callback``.
        :return: ``Task``
        """
        if name in self._tasks:
            raise ValueError(f'A Task with the name "{name}" already exists.')
        self._tasks[name] = Task(name, callback, delay, with_dt, args, kwargs)
        return self._tasks[name]

    def remove_task(self, name):
        """Remove Task ``name`` from the TaskManager."""
        if name in self._tasks:
            self._tasks.pop(name).disable()

    def __call__(self):
        """Calls all registered ``Task`` instances."""
        clk = time.perf_counter()
        for task in self._tasks.values():
            task(clk)

    def __getitem__(self, item):
        # type: (str) -> Task
        if item in self._tasks:
            return self._tasks[item]
        raise IndexError(f'No task named "{item}"')
