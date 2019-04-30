"""
Unittests for engine.taskmanager
"""
import time

from engine import taskmanager

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


def test_taskmanager():
    def callback_no_dt(arg_a, arg_b, _=None, kwarg_a='blah'):
        assert arg_a == 'a'
        assert arg_b == 'b'
        assert kwarg_a == 'kwa'

    def callback_dt(dt):
        assert dt
    tm = taskmanager.TaskManager()
    _ = tm.add_task(
        'test_task_no_dt', callback_no_dt, 0, False, 'a', 'b', kwarg_a='kwa'
    )
    _ = tm.add_task('test_task_dt', callback_dt)
    tm()


def test_timing():
    def callback(counter):
        counter.append(1)

    cb_counter = []
    tm = taskmanager.TaskManager()
    task = tm.add_task(
        'counter_task', callback, 0.02, False, cb_counter
    )
    start_time = task._last_exec  # time.perf_counter()
    while time.perf_counter() - start_time < 1:
        tm()
    assert sum(cb_counter) == 49
