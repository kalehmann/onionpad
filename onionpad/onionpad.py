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

"""Base classes for the Onionpad implementation."""

try:
    from typing import Dict, List, Type
except ImportError as _:
    pass

import time

from adafruit_macropad import MacroPad
from displayio import Group
import keypad
from .hid import _Code, Key, ConsumerControl, MouseClick, MouseMove
from .layout import TitleLayout
from .util import LayeredMap


class ActionRunner:
    """Executes actions for the macropad.

    Actions are simple callables or input that is send to the host, for example
    key presses or mouse movement.

    :param macropad: The macropad instance.
    """

    def __init__(self, macropad: MacroPad):
        self._macropad = macropad

    def execute_hid_action(self, action: _Code | MouseMove | str) -> None:
        """
        :param action: The action that will be executed.
                       Either an instance of :class:`onionpad.hid._Code`,
                       a :class:`onionpad.hid.MouseMove` or a string.
                       If the action is a string, every character of the string
                       will be send as key press to the host.
        """
        if isinstance(action, ConsumerControl):
            self._macropad.consumer_control.send(action.code)
        elif isinstance(action, Key):
            if action.release:
                self._macropad.keyboard.release(action.code)
            else:
                self._macropad.keyboard.press(action.code)
        elif isinstance(action, MouseClick):
            if action.release:
                self._macropad.mouse.release(action.code)
            else:
                self._macropad.mouse.press(action.code)
        elif isinstance(action, MouseMove):
            self._macropad.mouse.move(
                x=action.delta_x,
                y=action.delta_y,
                wheel=action.delta_wheel,
            )
        elif isinstance(action, str):
            self._macropad.keyboard_layout.write(action)

    def execute(
        self,
        action,
        args: dict | None = None,
        release: bool = True,
    ) -> None:
        """Executes an action.

        :param action: Is the action the should be executed.
                       If action is callable it will be simply called.
                       A string will be entered on the keyboard.
                       Instances of :class:`onionpad.hid.ConsumerControl`,
                       :class:`onionpad.hid.Key`,
                       :class:`onionpad.hid.MouseClick` or
                       :class:`onionpad.hid.MouseMove` will be send to the
                       host.
                       In case the action is an iterable, each element will
                       be executed as action.
        :param args: Additional keyword arguments that will be passed to the
                     action.
        :param release: Whether to tell the host, that all keys and consumer
                        control functions are released again after the action
                        was executed.
        """
        if args is None:
            args = {}
        if callable(action):
            action(**args)
        elif isinstance(action, (_Code, MouseMove, str)):
            self.execute_hid_action(action)
        elif isinstance(action, list):
            for element in action:
                self.execute(element, release=False)
        if release:
            self.release_all()

    def release_all(self) -> None:
        """Report all key presses and mouse clicks to the host as released."""
        self._macropad.consumer_control.release()
        self._macropad.keyboard.release_all()
        self._macropad.mouse.release_all()


class Mode:
    """A layer for the OnionPad that can define key events, show content on the
    display or send events to the host.

    :param onionPad: The OnionPad instance.
    """

    _HIDDEN = False
    NAME = "Mode"
    """The name of the mode that will be used in the mode selection."""

    def __init__(self, onionpad: "OnionPad"):
        self.onionpad = onionpad

    @property
    def group(self) -> Group | None:
        """
        :returns: A :class:`displayio.Group` that will be shown on the display.
        """
        return None

    @classmethod
    def is_hidden(cls) -> bool:
        """
        :returns: Whether this mode should be hidden from the user.
        """
        return cls._HIDDEN

    @property
    def keydown_actions(self) -> list:
        """
        :returns: A 2-dimensional 4x3 list with actions that will be executed
                  when a key on the OnionPad is pressed.

                  See :meth:`ActionRunner.execute` for possible actions.
        """
        return [[None, None, None, None] for _ in range(3)]

    @property
    def keypad_icons(self) -> list:
        """
        :returns: A 2-dimensional 4x3 list with icons for actions registered
                  by this mode.
        """
        return [[None, None, None, None] for _ in range(3)]

    @property
    def keyup_actions(self) -> list:
        """
        :returns: A 2-dimensional 4x3 list with actions that will be executed
                  when a key on the OnionPad is released.

                  See :meth:`ActionRunner.execute` for possible actions.
        """
        return [[None, None, None, None] for _ in range(3)]

    @property
    def encoder_actions(self) -> list:
        """
        :returns: A 2-dimensional 1x1 list with actions that will be executed
                  when the rotatory encoder changes its state.
        """
        return [[None]]

    @property
    def title(self) -> str | None:
        """
        :returns: The title of the mode that will be shown on the display of the
                  OnionPad.
        """
        return None

    def start(self) -> None:
        """Called when the mode is activated."""

    def pause(self) -> None:
        """Called when a mode is suspended."""

    def tick(self) -> None:
        """Called periodically. Can be used to update the display or change
        the LEDs.
        """


class ModeContainer:
    """Container for modes.

    Keeps track of all registered modes and avoids instanciating them twice.
    """

    def __init__(self):
        self._modes: Dict[Type[Mode], Mode] = {}

    @property
    def modes(self) -> tuple:
        """
        :returns: A tuple with the classes of all modes in the container.
        """
        return tuple(self._modes.keys())

    def add(self, mode: Mode) -> None:
        """Add a mode to the container.

        :param mode: The mode that should be added to the container.
                     If another instance of the same mode is already stored in
                     the container, nothing will happen.
        """
        mode_class = type(mode)
        if mode_class in self:
            return
        self._modes[mode_class] = mode

    def __contains__(self, mode_class: type[Mode]) -> bool:
        """Check if the container has an instance of a specific mode class.

        :param mode_class: The class whose existence in the container is checked.
        :returns: Whether the container has an instance of that class.
        """
        return mode_class in self._modes

    def __getitem__(self, mode_class: type[Mode]) -> Mode:
        """Get an instance for a mode class.

        :param mode_class: The class for which an instance should be returned.
        :returns: The instance of the class.
        """
        if mode_class not in self:
            raise KeyError(
                f"The modecontainer has no instance of {mode_class.__class__}"
            )
        return self._modes[mode_class]


class ModeStack:
    """The stack of all active modes.

    :param layout: The title layout of the OnionPad.
    """

    def __init__(self, layout: TitleLayout):
        self._active_modes: List[Mode] = []
        self._default_mode: Mode | None = None
        self._encoder_actions = LayeredMap(1, 1)
        self._keydown_actions = LayeredMap(4, 3)
        self._keyup_actions = LayeredMap(4, 3)
        self._keypad_icons = LayeredMap(4, 3)
        self._layout = layout

    @property
    def active_modes(self) -> tuple:
        """
        :returns: A tuple of the active modes in the reverse order of which
                  the modes where pushed onto the stack.
        """
        return tuple(reversed(self._active_modes))

    @property
    def encoder_actions(self) -> tuple:
        """
        :returns: A 2-dimensional 1x1 tuple with actions for the rotary encoder.
        """
        return self._encoder_actions.immutable

    @property
    def keydown_actions(self) -> tuple:
        """
        :returns: A 2-dimensional 4x3 tuple with the keydown actions.
        """
        return self._keydown_actions.immutable

    @property
    def keyup_actions(self) -> tuple:
        """
        :returns: A 2-dimensional 4x3 tuple with the keyup actions.
        """
        return self._keyup_actions.immutable

    @property
    def keypad_icons(self) -> tuple:
        """
        :returns: A 2-dimensional 4x3 tuple with the icons for the hotkeys.
        """
        return self._keypad_icons.immutable

    def pop(self, mode: Mode | None = None) -> None:
        """
        Removes a mode from a stack.

        If `mode` is provided and not `None`, all modes that are above of
        `mode` on the mode stack will be removed too.

        :param mode: Is the mode that will be removed from the modestack.
                     Provide None to remove the mode at the top of the stack.
        """
        if mode:
            if mode not in self._active_modes:
                return
            while self._active_modes[-1] != mode:
                self.pop()
            self.pop()

            return
        mode = self._active_modes.pop()
        mode.pause()
        if mode.group is not None:
            self._layout.remove(mode.group)
        self._encoder_actions.remove_layer(mode.NAME)
        self._keydown_actions.remove_layer(mode.NAME)
        self._keypad_icons.remove_layer(mode.NAME)
        self._keyup_actions.remove_layer(mode.NAME)
        for active_mode in reversed(self._active_modes):
            if active_mode.title:
                self._layout.title = active_mode.title
                break
        else:
            self._layout.title = None
        if not self._active_modes and self._default_mode:
            self.push(self._default_mode)

    def push(self, mode: Mode) -> None:
        """
        Adds a mode to the modestack.

        Each mode can occur exactly once on the modestack. If an instance of
        `mode_class` already is on the modestack, all modes on the modestack
        above it will be removed and the mode will be re-initialized.

        :param mode: The mode that should be placed on top of the modestack.
        """
        if mode in self._active_modes:
            self.pop(mode)
        mode.start()
        self._active_modes.append(mode)
        if mode.title:
            self._layout.title = mode.title
        if mode.group is not None:
            self._layout.append(mode.group)
        self._encoder_actions.push_layer(mode.encoder_actions, mode.NAME)
        self._keydown_actions.push_layer(mode.keydown_actions, mode.NAME)
        self._keyup_actions.push_layer(mode.keyup_actions, mode.NAME)
        self._keypad_icons.push_layer(mode.keypad_icons, mode.NAME)

    def set_default_mode(self, mode: Mode | None) -> None:
        """Set the default mode to apply if all other modes are removed.

        :param mode: The new default mode.
        """
        self._default_mode = mode
        if mode and not self._active_modes:
            self.push(mode)

    def set_mode(self, mode: Mode) -> None:
        """
        Set the mode of the OnionPad.

        All other modes will be removed from the modestack and the provided mode
        will be the only element on the modestack.

        :param mode: The new mode of the OnionPad
        """
        while self._active_modes:
            self.pop()
        self.push(mode)


class OLEDSaver:
    """Automatically put the OLED display to sleep after inactivity.

    :param onionpad: The onionpad instance.
    """

    def __init__(self, macropad: MacroPad):
        self._delay = 30.0
        self._last_input = time.monotonic()
        self._macropad = macropad
        self._sleep = False

    @property
    def delay(self) -> float:
        """
        :returns: The period of inactivity until the display is put asleep.
        """
        return self._delay

    @delay.setter
    def delay(self, value: float) -> None:
        """Set the period of inactivity until the display is put asleep.

        :param value: The period of inactivity until the display is put asleep.
        """
        self._delay = value
        self.tick(False)

    @property
    def is_asleep(self) -> bool:
        """
        :returns: Whether the display is currently off.
        """
        return self._sleep

    def sleep(self) -> None:
        """Put the display to sleep."""
        if self.is_asleep:
            return
        self._macropad.display_sleep = True
        self._sleep = True

    def tick(self, user_input: bool) -> None:
        """

        :param user_input: Whether there was any user input after the last call
                           to this method.
        """
        now = time.monotonic()
        if user_input:
            self._last_input = now
            self.wakeup()
        elif now - self._last_input > self._delay and not self.is_asleep:
            self.sleep()

    def wakeup(self) -> None:
        """Wakes the display up."""
        if not self.is_asleep:
            return
        self._macropad.display_sleep = False
        self._sleep = False


class OnionPad:
    """The OnionPad is a CircuitPython firmware for the Adafruit Macropad.

    Its functionality is grouped in modes, of which multiple can be active at
    once. The active modes are placed as layers on a stack. In case of any
    event, such as a key press, the stack is parsed from top to bottom until a
    mode handles the event.
    """

    def __init__(self):
        self._encoder_position = 0
        self._macropad: MacroPad = None
        self._mode_container = ModeContainer()
        self._modestack: ModeStack = None
        self._oled_saver: OLEDSaver = None
        self._should_refresh_display = False
        self._should_refresh_pixels = False
        self._setup_macropad()

    @property
    def keypad_icons(self) -> tuple:
        """
        :returns: A 2-dimensional 4x3 tuple with the icons for the hotkeys.
        """
        return self._modestack.keypad_icons

    @property
    def macropad(self) -> MacroPad:
        """
        :returns: The helper for the macropad.
        """
        return self._macropad

    @property
    def modes(self) -> tuple:
        """
        :returns: All registered modes.
        """
        return tuple(self._mode_container.modes)

    def execute_action(
        self,
        action,
        args: dict | None = None,
        release: bool = True,
    ) -> None:
        """Wrapper around :meth:`ActionRunner.execute`."""
        ActionRunner(self._macropad).execute(action, args=args, release=release)

    def pop_mode(self, mode: Mode | None = None) -> None:
        """
        Removes a mode from a stack.

        If `mode` is provided and not `None`, all modes that are above of
        `mode` on the mode stack will be removed too.

        :param mode: Is the mode that will be removed from the modestack.
                     Provide None to remove the mode at the top of the stack.
        """
        self._modestack.pop(mode)
        self.schedule_display_refresh()

    def push_mode(self, mode_class: type[Mode]) -> None:
        """
        Adds a mode to the modestack.

        Each mode can occur exactly once on the modestack. If an instance of
        `mode_class` already is on the modestack, all modes on the modestack
        above it will be removed and the mode will be re-initialized.

        :param mode_class: is the class of the mode that should be placed on top
                           of the modestack.
        """
        if mode_class not in self._mode_container:
            self._mode_container.add(mode_class(self))
        mode = self._mode_container[mode_class]
        self._modestack.push(mode)
        self.schedule_display_refresh()

    def register_mode(self, mode_class: type[Mode]) -> None:
        """
        Register a mode, so that it shows up in the mode selection.

        :param mode_class: The class of the mode that should be registered.
        """
        if mode_class not in self._mode_container:
            self._mode_container.add(mode_class(self))

    def set_default_mode(self, mode_class: type[Mode] | None) -> None:
        """Set the mode that will be applied when no other mode is active.

        :param mode_class: The new default mode.
        """
        if not mode_class:
            self._modestack.set_default_mode(None)

            return
        self.register_mode(mode_class)
        mode = self._mode_container[mode_class]
        if not self._modestack.active_modes:
            self.schedule_display_refresh()
        self._modestack.set_default_mode(mode)

    def set_mode(self, mode_class: type[Mode]) -> None:
        """
        Set the mode of the OnionPad.

        All other modes will be removed from the modestack and the provided mode
        will be the only element on the modestack.

        :param mode_class: The new mode of the OnionPad
        """
        if mode_class not in self._mode_container:
            self._mode_container.add(mode_class(self))
        mode = self._mode_container[mode_class]
        self._modestack.set_mode(mode)

    def schedule_display_refresh(self) -> None:
        """Notify the OnionPad that the display content has changed."""
        self._should_refresh_display = True

    def schedule_pixel_refresh(self) -> None:
        """Notify the OnionPad that the NeoPixels have changed."""
        self._should_refresh_pixels = True

    def run(self) -> None:
        """Starts the OnionPad."""
        while True:
            self._tick()

    def _tick(self) -> None:
        user_input = False
        while self.macropad.keys.events:
            user_input = True
            self._handle_key_event(self.macropad.keys.events.get())
        encoder = self.macropad.encoder
        encoder_change = encoder - self._encoder_position
        self._encoder_position = encoder
        if encoder_change:
            user_input = True
            self.execute_action(
                self._modestack.encoder_actions[0][0],
                args={"encoder": encoder, "change": encoder_change},
            )
        # Copy the list of modes to avoid problems with changes to the mode list
        # during iteration.
        for mode in self._modestack.active_modes:
            mode.tick()
        if self._should_refresh_display:
            self.macropad.display.refresh()
            self._should_refresh_display = False
        if self._should_refresh_pixels:
            self.macropad.pixels.show()
            self._should_refresh_pixels = False
        self._oled_saver.tick(user_input)

    def _handle_key_event(self, event: keypad.Event) -> None:
        """Runs the first action on the modestack that matches a keypad event.

        :param event: The keypad event.
        """
        column = event.key_number % 4
        row = event.key_number // 4
        if event.pressed:
            action = self._modestack.keydown_actions[row][column]
        else:
            action = self._modestack.keyup_actions[row][column]
        self.execute_action(action)

    def _setup_macropad(self) -> None:
        macropad = MacroPad(rotation=90)
        macropad.display.auto_refresh = False
        macropad.display.brightness = 0.2
        macropad.pixels.auto_write = False
        layout = TitleLayout(macropad.display.width)
        macropad.display.show(layout)
        self.schedule_display_refresh()

        self._macropad = macropad
        self._modestack = ModeStack(layout)
        self._oled_saver = OLEDSaver(macropad)
