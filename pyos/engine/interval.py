"""
Provides various Interval classes to animate a NodePath.
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


class Interval(object):  # TODO: Update to use NodePath
    """
    Base class for Intervals.

    :param entity: The NodePath to animate
    :param depth:
    :param duration: The duration of the interval.
    """
    def __init__(self, entity, depth, duration):
        self.__entity__ = entity
        self.__depth__ = depth
        if duration < 0.005:
            duration = 0.005
        self.__duration__ = duration
        self.__time__ = 0.0
        self.__norm_time__ = 1.0 / duration

    @property
    def entity(self):
        return self.__entity__

    @property
    def depth(self):
        return self.__depth__

    @property
    def duration(self):
        return self.__duration__

    @property
    def time(self):
        return self.__time__

    @property
    def norm_time(self):
        return self.__norm_time__

    @time.setter
    def time(self, value):
        if not isinstance(value, float) or value < 0:
            raise ValueError('Expected value of type float')
        self.__time__ = value


class PositionInterval(Interval):
    """
    Moves a NodePath between a start and end position in a specified duration.

    :param entity: The NodePath to animate
    :param depth:
    :param duration: The duration of the interval.
    :param start_pos: The start position.
    :param end_pos: The end position.
    """

    def __init__(self, entity, depth, duration, start_pos, end_pos):
        super(PositionInterval, self).__init__(entity, depth, duration)
        self.__start_pos__ = start_pos
        self.__end_pos__ = end_pos
        self.__delta__ = end_pos - start_pos

    @property
    def start_pos(self):
        return self.__start_pos__

    @property
    def end_pos(self):
        return self.__end_pos__

    @property
    def delta(self):
        return self.__delta__

    def step(self, dt):
        """Return the remaining time and performs a lerp step"""
        self.time = self.time + dt
        if self.time > self.duration:
            x, y = self.end_pos.asint()
        else:
            v = self.start_pos + self.time * self.norm_time * self.delta
            x, y = v.asint()
        self.entity.sprite.position = x, y
        self.entity.sprite.depth = self.depth
        return self.duration - self.time
