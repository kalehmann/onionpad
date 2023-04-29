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
    from typing import Dict
except ImportError as _:
    pass

from adafruit_hid import consumer_control_code, keycode


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


class _CodeWrapper:  # pylint: disable=too-few-public-methods
    """A simple wrapper around a class with consumer control or key code
    constants.

    :param code_provider: Either the class
                          `adafruit_hid.consumer_control_code.ConsumerControlCode`
                          or the class `adafruit_hid.keycode.Keycode`.
    :param code_class: Either the class `ConsumerControl` or the class `Key`.
    """

    def __init__(self, code_provider, code_class: type[_Code]):
        self._provider = code_provider
        self._cache: Dict[str, ConsumerControl | Key] = {}
        self._code_class = code_class

    def __getattr__(self, name: str) -> ConsumerControl | Key:
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
Keycode = _CodeWrapper(keycode.Keycode, Key)
