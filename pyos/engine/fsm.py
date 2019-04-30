"""
[WIP] Finite State Machine...
"""

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


class FSM(object):
    """
    Rudimentary Finite State Machine to organize state changes.
    Takes 1 - n objects from different classes that provide both a enter
    and exit method, that manage setup/cleanup for their state.
    Warning: There are no safeguards in place that prevent the app from crashing
    if the code in either enter or exit raises an Error.
    """
    def __init__(self):
        self._states = {}
        self._active_state = None

    def add_state(self, obj):
        """
        Adds a new state to the FSM. If an object of the same class already is
        present, it will be overwritten!

        :object obj: The class instance containing the enter and exit methods.
        """
        try:
            dir(obj).index('enter')
            dir(obj).index('exit')
        except ValueError:
            raise ValueError('Argument obj must contain "enter" and "exit" '
                             'methods.')
        if not (callable(obj.enter) and callable(obj.exit)):
            raise ValueError('Argument obj must contain "enter" and "exit" '
                             'methods.')
        k = type(obj).__name__.lower()
        self._states[k] = obj

    def request(self, state_name):
        sn = state_name.lower()
        if sn not in self._states:
            raise ValueError(f'No state with state with name "{state_name}" '
                             f'registered.')
        if self._active_state is not None:
            self._states[self._active_state].exit()
        self._states[state_name].enter()
        self._active_state = state_name
