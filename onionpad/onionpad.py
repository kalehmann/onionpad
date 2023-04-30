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

from adafruit_macropad import MacroPad
from displayio import Group
import keypad
from .hid import Key, ConsumerControl
from .layout import TitleLayout
from .util import LayeredMap


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
    def keydown_events(self) -> list:
        """
        :returns: A 2-dimensional 4x3 list with handlers that will be executed
                  when a key on the OnionPad is pressed.

                  See :meth:`OnionPad._exec_event_handler` for possible handlers.
        """
        return [[None, None, None, None] for _ in range(3)]

    @property
    def keypad_icons(self) -> list:
        """
        :returns: A 2-dimensional 4x3 list with icons for handlers registered
                  by this mode.
        """
        return [[None, None, None, None] for _ in range(3)]

    @property
    def keyup_events(self) -> list:
        """
        :returns: A 2-dimensional 4x3 list with handlers that will be executed
                  when a key on the OnionPad is released.

                  See `onion_pad.OnionPad._execEventHandler` for possible
                  handlers.
        """
        return [[None, None, None, None] for _ in range(3)]

    @property
    def encoder_events(self) -> list:
        """
        :returns: A 2-dimensional 1x1 list with handlers that will be executed
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
        self._encoder_handlers = LayeredMap(1, 1)
        self._keydown_handlers = LayeredMap(4, 3)
        self._keyup_handlers = LayeredMap(4, 3)
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
    def encoder_handlers(self) -> tuple:
        """
        :returns: A 2-dimensional 1x1 tuple with handler for the rotary encoder.
        """
        return self._encoder_handlers.immutable

    @property
    def keydown_handlers(self) -> tuple:
        """
        :returns: A 2-dimensional 4x3 tuple with the keydown event handlers.
        """
        return self._keydown_handlers.immutable

    @property
    def keyup_handlers(self) -> tuple:
        """
        :returns: A 2-dimensional 4x3 tuple with the keyup event handlers.
        """
        return self._keyup_handlers.immutable

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
        if mode.encoder_events:
            self._encoder_handlers.remove_layer(mode.NAME)
        if mode.keydown_events:
            self._keydown_handlers.remove_layer(mode.NAME)
        if mode.keypad_icons:
            self._keypad_icons.remove_layer(mode.NAME)
        if mode.keyup_events:
            self._keyup_handlers.remove_layer(mode.NAME)
        for active_mode in reversed(self._active_modes):
            if active_mode.title:
                self._layout.title = active_mode.title
                break
        else:
            self._layout.title = None

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
        self._encoder_handlers.push_layer(mode.encoder_events, mode.NAME)
        self._keydown_handlers.push_layer(mode.keydown_events, mode.NAME)
        self._keyup_handlers.push_layer(mode.keyup_events, mode.NAME)
        self._keypad_icons.push_layer(mode.keypad_icons, mode.NAME)

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


class OnionPad:
    """The OnionPad is a CircuitPython firmware for the Adafruit Macropad.

    Its functionality is grouped in modes, of which multiple can be active at
    once. The active modes are placed as layers on a stack. In case of any
    event, such as a key press, the stack is parsed from top to bottom until a
    mode handles the event.
    """

    def __init__(self):
        self._encoder_position = 0
        self._macropad = None
        self._mode_container = ModeContainer()
        self._modestack = None
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
        while self.macropad.keys.events:
            self._handle_key_event(self.macropad.keys.events.get())
        encoder = self.macropad.encoder
        encoder_change = encoder - self._encoder_position
        self._encoder_position = encoder
        if encoder_change:
            self._exec_event_handler(
                self._modestack.encoder_handlers[0][0],
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

    def _handle_key_event(self, event: keypad.Event) -> None:
        """Runs the first handler on the modestack that matches a keypad event.

        :param event: The keypad event.
        """
        column = event.key_number % 4
        row = event.key_number // 4
        if event.pressed:
            handler = self._modestack.keydown_handlers[row][column]
        else:
            handler = self._modestack.keyup_handlers[row][column]
        self._exec_event_handler(handler)

    def _exec_event_handler(
        self,
        handler,
        args: dict | None = None,
        release: bool = True,
    ) -> None:
        """Executes an event handler.

        :param handler: Is the handler the should be executed.
                        If handler is callable it will be simply called.
                        A string will be entered on the keyboard.
                        Instances of `onion_pad.hid.ConsumerControl` or
                        `onion_pad.hid.Key` will be send to the host.
                        In case the handler is an iterable, each element will
                        be executed as handler.
        :param args: Additional keyword arguments that will be passed to the
                     handler.
        :param release: Whether to tell the host, that all keys and consumer
                        control functions are released again after the handler
                        was executed.
        """
        if args is None:
            args = {}
        if callable(handler):
            handler(**args)
        elif isinstance(handler, str):
            self.macropad.keyboard_layout.write(handler)
        elif isinstance(handler, ConsumerControl):
            self.macropad.consumer_control.send(handler.code)
        elif isinstance(handler, Key):
            if handler.release:
                self.macropad.keyboard.release(handler.code)
            else:
                self.macropad.keyboard.press(handler.code)
        elif isinstance(handler, list):
            for element in handler:
                self._exec_event_handler(element, release=False)
        if release:
            self.macropad.keyboard.release_all()
            self.macropad.consumer_control.release()

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
