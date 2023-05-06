#! /usr/bin/env python3
# Copyright (c) 2023 by Karsten Lehmann <mail@kalehmann.de>
#
#    This file is part of OnionPad.
#
#    OnionPad is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    OnionPad is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    long with OnionPad. If not, see <http://www.gnu.org/licenses/>.

"""Enables differentiation between consumer control and key codes by wrapping
them with objects.
"""

try:
    from typing import Dict, Tuple
except ImportError as _:
    pass

import math
import random

from adafruit_hid import consumer_control_code, keycode, mouse


class _Code:
    """Simple dataclass for wrapping consumer control or key codes.
    Can be use to check with `ininstance(code, ...)` if a code should be send as
    normal key press or consumer control key press.

    :param code: the code wrapped by this object.
    """

    def __init__(self, code: int):
        self._code = code
        self.release = False

    @property
    def code(self) -> int:
        """
        :returns: The key or consumer control code.
        """
        return self._code

    def __neg__(self):
        """Implement negation to mark a consumer control or keycode as release
        of the key instead of a press.
        """
        negated = type(self)(self._code)
        negated.release = not self.release

        return negated


class ConsumerControl(_Code):  # pylint: disable=too-few-public-methods
    """Check with `isinstance(code, ConsumerControlCode)`"""


class Key(_Code):  # pylint: disable=too-few-public-methods
    """Check with `isinstance(code, KeyCode)`"""


class MouseClick(_Code):  # pylint: disable=too-few-public-methods
    """Check with `isinstance(code, MouseClick)`"""


class MouseMove:
    """Dataclass for mouse movements.
    tracks differences in the position and wheel movement.

    :param delta_x: The horizontal movement.
    :param delta_y: The vertical movement.
    :param delta_wheel: The movement of the mouse wheel.
    """

    def __init__(self, delta_x: int = 0, delta_y: int = 0, delta_wheel: int = 0):
        self._delta_x = delta_x
        self._delta_y = delta_y
        self._delta_wheel = delta_wheel

    @property
    def delta_x(self) -> int:
        """
        :returns: The movement on the horizontal axis.
        """
        return self._delta_x

    @property
    def delta_y(self) -> int:
        """
        :returns: The movement on the vertical axis.
        """
        return self._delta_y

    @property
    def delta_wheel(self) -> int:
        """
        :returns: The movement of the mouse wheel.
        """
        return self._delta_wheel


class _CodeWrapper:  # pylint: disable=too-few-public-methods
    """A simple wrapper around a class with consumer control or key code
    constants.

    :param code_provider: Either the class
                          :class:`adafruit_hid.consumer_control_code.ConsumerControlCode`,
                          :class:`adafruit_hid.keycode.Keycode` or the class
                          :class:`adafruit_hid.mouse.Mouse`.
    :param code_class: One of the classes :class:`ConsumerControl`, :class:`Key`
                       or :class:`MouseClick`.
    """

    def __init__(self, code_provider, code_class: type[_Code]):
        self._provider = code_provider
        self._cache: Dict[str, ConsumerControl | Key | MouseClick] = {}
        self._code_class = code_class

    def __getattr__(self, name: str) -> ConsumerControl | Key | MouseClick:
        if name in self._cache:
            return self._cache[name]
        code = getattr(self._provider, name, None)
        if code is None:
            if isinstance(self._provider, type):
                classname = self._provider.__name__
                raise AttributeError(f"Class `{classname}` has no attribute `{name}`.")
            classname = type(self._provider).__name__
            raise AttributeError(
                f"Object of class `{classname}` has no attribute `{name}`."
            )
        code = self._code_class(code)
        self._cache[name] = code

        return code


ConsumerControlCode = _CodeWrapper(
    consumer_control_code.ConsumerControlCode,
    ConsumerControl,
)
"""Wrapper around :class:`adafruit_hid.consumer_control_code.ConsumerControlCode`."""
Keycode = _CodeWrapper(keycode.Keycode, Key)
"""Wrapper around :class:`adafruit_hid.keycode.Keycode`."""
Mouse = _CodeWrapper(mouse.Mouse, MouseClick)
"""Wrapper around :class:`adafruit_hid.mouse.Mouse`."""


class MouseJiggler:
    """A simple moise jiggler.

    :param pixels_per_second: Is an approximation for the numbers of points the
                              per second cursor will move per second.
                              Note that the host may convert points to pixels
                              with a factor different from one.
    """

    def __init__(self, pixels_per_second: int = 100):
        self._deviation = random.uniform(0, 2 * math.pi)
        self._deviation_target = random.uniform(0, 2 * math.pi)
        self._pixels_per_second = pixels_per_second
        self._position: Tuple[int, int] = (0, 0)
        self._sleep = 0.0
        self._target: Tuple[int, int] = self._get_next_target()

    @property
    def position(self) -> Tuple[int, int]:
        """
        :returns: The mouse pointers position relative to its initial position.
        """
        return self._position

    def update(self, delta_t: float) -> Tuple[int, int]:
        """
        :param delta_t:
        """
        if self._sleep > delta_t:
            self._sleep -= delta_t

            return (0, 0)
        delta_x = self._target[0] - self._position[0]
        delta_y = self._target[1] - self._position[1]
        distance = math.sqrt(abs(delta_x) ** 2 + abs(delta_y) ** 2)
        pixels = self._pixels_per_second * delta_t
        if pixels >= distance:
            self._sleep = random.uniform(15, 30)
            self._target = self._get_next_target()

            return (delta_x, delta_y)
        deviation = self._update_deviation(delta_t)
        delta_x = round(delta_x * pixels / distance + deviation[0])
        delta_y = round(delta_y * pixels / distance + deviation[1])
        self._position = (
            self._position[0] + delta_x,
            self._position[1] + delta_y,
        )

        return (delta_x, delta_y)

    def _update_deviation(self, delta_t) -> Tuple[int, int]:
        """
        :param delta_t:
        """
        deviation_points = self._pixels_per_second * delta_t * 0.5
        rotation_points = self._pixels_per_second * delta_t * 0.1
        if abs(self._deviation_target - self._deviation) < rotation_points:
            self._deviation_target = random.uniform(0, 2 * math.pi)
        self._deviation += math.copysign(
            rotation_points, self._deviation_target - self._deviation
        )

        return (
            (math.cos(self._deviation) - math.sin(self._deviation)) * deviation_points,
            (math.sin(self._deviation) + math.cos(self._deviation)) * deviation_points,
        )

    def _get_next_target(self) -> Tuple[int, int]:
        return (
            random.randint(-50, 50),
            random.randint(-50, 50),
        )
