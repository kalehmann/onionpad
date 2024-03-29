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

"""Basic modes for the Onionpad."""

try:
    from collections.abc import Sequence
    from typing import Type
except ImportError as _:
    pass

import random
import time

from displayio import Group
from .animation import Animation, LoadingCircle, TileAnimation
from .assets import Icons
from .hid import ConsumerControlCode, MouseJiggler, MouseMove
from .layout import HotkeyMap, SelectionLayout
from .onionpad import Mode, OnionPad
from .util import hsv_to_packed_rgb, LayeredMap


class AmbientMode(Mode):
    """Changes the colors of the NeoPixels continually."""

    NAME = "Ambience"

    def __init__(self, onionpad: OnionPad):
        super().__init__(onionpad)
        self.keys = [
            [
                random.random(),  # Hue in [0, 1]
                0.2 * random.random() + 0.8,  # Saturation in [0.8, 1]
                random.choice((-1, 1)) * 0.2 * random.random() + 0.2,
            ]
            for _ in range(12)
        ]
        self._last_run = 0.0

    def start(self) -> None:
        self._last_run = time.monotonic()

    def pause(self) -> None:
        for i in range(12):
            self.onionpad.macropad.pixels[i] = 0x000000
        self.onionpad.schedule_pixel_refresh()

    def tick(self) -> None:
        now = time.monotonic()
        delta_t = now - self._last_run
        self._last_run = now
        for i in range(12):
            self.keys[i][0] = (self.keys[i][0] + self.keys[i][2] * delta_t) % 1
            self.onionpad.macropad.pixels[i] = hsv_to_packed_rgb(
                self.keys[i][0],
                self.keys[i][1],
                0.2,
            )
        self.onionpad.schedule_pixel_refresh()


class BaseMode(Mode):
    """A simple mode that can trigger the mode selection."""

    NAME = "Base Mode"

    def __init__(self, onionpad: OnionPad):
        super().__init__(onionpad)
        self._layer_icon = Icons.generic.layers()

    @property
    def title(self) -> str | None:
        return self.NAME

    @property
    def keydown_actions(self) -> Sequence:
        return [
            [self._on_layer_select, None, None, None],
            [None, None, None, None],
            [None, None, None, None],
        ]

    @property
    def keypad_icons(self) -> Sequence:
        return [
            [self._layer_icon, None, None, None],
            [None, None, None, None],
            [None, None, None, None],
        ]

    def _on_layer_select(self):
        self.onionpad.push_mode(PreSelectionMode)


class ModeGroup(Mode):
    """Base class for a mode that groups several other modes.

    Extend this class and fill the :attr:`MODES` class attribute to create a
    group of modes.
    There is no need to override any other method or attribute.

    Example ::

        class MyGroup(ModeGroup):
            MODES = [BaseMode, HotkeyMapMode, MediaMode, MouseJigglerMode]
    """

    MODES: list[Type[Mode]] = []
    """The list of modes in this group."""

    NAME = "Group"

    def __init__(self, onionpad: OnionPad):
        super().__init__(onionpad)
        self._encoder_actions = LayeredMap(1, 1)
        self._keydown_actions = LayeredMap(4, 3)
        self._keypad_icons = LayeredMap(4, 3)
        self._keyup_actions = LayeredMap(4, 3)
        self._layer = Group(x=0, y=0)
        self._modes = []
        for mode_class in self.MODES:
            mode = mode_class(onionpad)
            self._encoder_actions.push_layer(mode.encoder_actions, mode.NAME)
            self._keydown_actions.push_layer(mode.keydown_actions, mode.NAME)
            self._keypad_icons.push_layer(mode.keypad_icons, mode.NAME)
            self._keyup_actions.push_layer(mode.keyup_actions, mode.NAME)
            self._modes.append(mode)
            if mode.group:
                self._layer.append(mode.group)

    @property
    def group(self) -> Group | None:
        return self._layer

    @property
    def keydown_actions(self) -> Sequence:
        return self._keydown_actions.immutable

    @property
    def keypad_icons(self) -> Sequence:
        return self._keypad_icons.immutable

    @property
    def keyup_actions(self) -> Sequence:
        return self._keyup_actions.immutable

    @property
    def encoder_actions(self) -> Sequence:
        return self._encoder_actions.immutable

    @property
    def title(self) -> str | None:
        return self.NAME

    def start(self) -> None:
        for mode in self._modes:
            mode.start()

    def pause(self) -> None:
        for mode in self._modes:
            mode.pause()

    def tick(self) -> None:
        for mode in self._modes:
            mode.tick()


class HotkeyMapMode(Mode):
    """Displays the icons for the hotkey actions."""

    NAME = "Hotkeys"

    def __init__(self, onionpad: OnionPad):
        super().__init__(onionpad)
        self._layer = HotkeyMap((0, 40))

    @property
    def group(self) -> Group | None:
        return self._layer

    def tick(self) -> None:
        if self._layer.set_contents(self.onionpad.keypad_icons):
            self.onionpad.schedule_display_refresh()


class MediaMode(Mode):
    """Add hotkeys for media actions."""

    NAME = "Media"

    def __init__(self, onionpad: OnionPad):
        super().__init__(onionpad)
        self._icons = {
            "next": Icons.generic.next(),
            "play": Icons.generic.play_pause(),
            "previous": Icons.generic.previous(),
            "stop": Icons.generic.stop(),
        }

    @property
    def keydown_actions(self) -> Sequence:
        return [
            [None, None, None, None],
            [
                ConsumerControlCode.SCAN_PREVIOUS_TRACK,
                ConsumerControlCode.PLAY_PAUSE,
                ConsumerControlCode.STOP,
                ConsumerControlCode.SCAN_NEXT_TRACK,
            ],
            [None, None, None, None],
        ]

    @property
    def keypad_icons(self) -> Sequence:
        return [
            [None, None, None, None],
            [
                self._icons["previous"],
                self._icons["play"],
                self._icons["stop"],
                self._icons["next"],
            ],
            [None, None, None, None],
        ]


class MouseJigglerMode(Mode):
    """Simulates mouse movement to the host."""

    _DURATION = 1.0
    NAME = "Jiggler"

    def __init__(self, onionpad: OnionPad):
        super().__init__(onionpad)
        bitmap_mouse = Icons.generic.mouse()
        bitmap_running = Icons.mouse()
        bitmap_sleeping = Icons.mouse_sleeping()

        self._active = False
        self._last_tick = 0.0
        self._layer = Group(x=0, y=0)
        self._layer.append(TileAnimation((40, 17), bitmap_running, (20, 15)))
        self._layer.append(TileAnimation((40, 17), bitmap_sleeping, (20, 15)))
        self._layer[0].hidden = True
        self._mouse_icon = bitmap_mouse
        self._mouse_jiggler = MouseJiggler()
        self._start = 0.0

    @property
    def group(self) -> Group:
        return self._layer

    @property
    def keydown_actions(self) -> Sequence:
        return [
            [None, None, None, self._toggle_jiggle],
            [None, None, None, None],
            [None, None, None, None],
        ]

    @property
    def keypad_icons(self) -> Sequence:
        return [
            [None, None, None, self._mouse_icon],
            [None, None, None, None],
            [None, None, None, None],
        ]

    def _toggle_jiggle(self):
        if self._active:
            # Enter inactive mode
            self._layer[0].hidden = True
            self._layer[1].hidden = False
        else:
            # Enter active mode
            self._layer[0].hidden = False
            self._layer[1].hidden = True
        self._active = not self._active

    def start(self):
        self._last_tick = time.monotonic()
        self._start = self._last_tick

    def tick(self) -> None:
        animation: Animation = self.group[0] if self._active else self.group[1]
        now = time.monotonic()
        progress = (now - self._start) / self._DURATION
        if self._active:
            delta_x, delta_y = self._mouse_jiggler.update(now - self._last_tick)
            self.onionpad.execute_action(MouseMove(delta_x, delta_y))
        if animation.update(progress % 1):
            self.onionpad.schedule_display_refresh()
        self._last_tick = now


class PreSelectionMode(Mode):
    """Shows a short animation before the selection of modes.

    If the mode selection key is released, before the animation finishes, the
    OnionPad is reverted to the default mode.
    """

    DURATION = 1
    _HIDDEN = True
    NAME = "Preselection"

    def __init__(self, onionpad: OnionPad):
        super().__init__(onionpad)
        self._start = 0.0
        self._layer = LoadingCircle()

    @property
    def group(self) -> Group:
        return self._layer

    @property
    def keyup_actions(self) -> Sequence:
        return [
            [self._abort, None, None, None],
            [None, None, None, None],
            [None, None, None, None],
        ]

    def start(self):
        self._start = time.monotonic()

    def tick(self) -> None:
        progress = (time.monotonic() - self._start) / self.DURATION
        if progress >= 1:
            self.onionpad.pop_mode(self)
            self.onionpad.push_mode(SelectionMode)

            return
        self.group.update(progress)
        self.onionpad.schedule_display_refresh()

    def _abort(self) -> None:
        self.onionpad.set_mode(None)


class SelectionMode(Mode):
    """Lists selectable modes and changes to the selected mode."""

    _HIDDEN = True
    NAME = "Selection"

    def __init__(self, onionpad: OnionPad):
        super().__init__(onionpad)
        display_width = onionpad.macropad.display.width
        self._modes = {
            mode.NAME: mode for mode in onionpad.modes if not mode.is_hidden()
        }
        self._layer = SelectionLayout(
            entries=list(self._modes.keys()),
            width=display_width,
        )

    @property
    def group(self) -> Group | None:
        return self._layer

    @property
    def encoder_actions(self) -> Sequence:
        return [[self._encoder]]

    @property
    def keydown_actions(self) -> Sequence:
        return [
            [lambda: None, None, None, None],
            [None, None, None, None],
            [None, None, None, None],
        ]

    @property
    def keyup_actions(self) -> Sequence:
        return [
            [self._select, None, None, None],
            [None, None, None, None],
            [None, None, None, None],
        ]

    @property
    def title(self) -> str | None:
        return "Modes:"

    # pylint: disable-next=unused-argument
    def _encoder(self, encoder: int, change: int) -> None:
        if change > 0:
            self._layer.next()
        else:
            self._layer.previous()
        self.onionpad.schedule_display_refresh()

    def _select(self) -> None:
        self.onionpad.pop_mode(self)
        if self._layer.active not in self._modes:
            return
        self.onionpad.push_mode(self._modes[self._layer.active])
