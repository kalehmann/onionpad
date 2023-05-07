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


import random
import time

from displayio import Group, OnDiskBitmap
from .onionpad import Mode, OnionPad
from .assets import Icons
from .hid import ConsumerControlCode, MouseJiggler, MouseMove
from .layout import Animation, HotkeyMap, LoadingCircle, SelectionLayout
from .util import hsv_to_packed_rgb


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
        self._layer_icon = OnDiskBitmap(Icons.generic.layers)
        self._layer_icon.pixel_shader.make_transparent(0)

    @property
    def title(self) -> str | None:
        return self.NAME

    @property
    def keydown_actions(self) -> list:
        return [
            [self._on_layer_select, None, None, None],
            [None, None, None, None],
            [None, None, None, None],
        ]

    @property
    def keypad_icons(self) -> list:
        return [
            [self._layer_icon, None, None, None],
            [None, None, None, None],
            [None, None, None, None],
        ]

    def _on_layer_select(self):
        self.onionpad.push_mode(PreSelectionMode)


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
            "next": OnDiskBitmap(Icons.generic.next),
            "play": OnDiskBitmap(Icons.generic.play_pause),
            "previous": OnDiskBitmap(Icons.generic.previous),
            "stop": OnDiskBitmap(Icons.generic.stop),
        }
        for bitmap in self._icons.values():
            bitmap.pixel_shader.make_transparent(0)

    @property
    def keydown_actions(self) -> list:
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
    def keypad_icons(self) -> list:
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
        bitmap_mouse = OnDiskBitmap(Icons.generic.mouse)
        bitmap_mouse.pixel_shader.make_transparent(0)
        bitmap_running = OnDiskBitmap(Icons.mouse)
        bitmap_running.pixel_shader.make_transparent(0)
        bitmap_sleeping = OnDiskBitmap(Icons.mouse_sleeping)
        bitmap_sleeping.pixel_shader.make_transparent(0)

        self._active = False
        self._last_tick = 0.0
        self._layer = Group(x=0, y=0)
        self._layer.append(Animation((40, 17), bitmap_running, (20, 15)))
        self._layer.append(Animation((40, 17), bitmap_sleeping, (20, 15)))
        self._layer[0].hidden = True
        self._mouse_icon = bitmap_mouse
        self._mouse_jiggler = MouseJiggler()
        self._start = 0.0

    @property
    def group(self) -> Group:
        return self._layer

    @property
    def keydown_actions(self) -> list:
        return [
            [None, None, None, self._toggle_jiggle],
            [None, None, None, None],
            [None, None, None, None],
        ]

    @property
    def keypad_icons(self) -> list:
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
        now = time.monotonic()
        progress = (now - self._start) / self._DURATION
        if self._active:
            animation = self.group[0]
            delta_x, delta_y = self._mouse_jiggler.update(now - self._last_tick)
            self.onionpad.execute_action(MouseMove(delta_x, delta_y))
        else:
            animation = self.group[1]
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
    def keyup_actions(self) -> list:
        return [
            [self._abort, None, None, None],
            [None, None, None, None],
            [None, None, None, None],
        ]

    def start(self):
        self._start = time.monotonic()
        self.group.reset()

    def tick(self) -> None:
        progress = (time.monotonic() - self._start) / self.DURATION
        if progress >= 1:
            self.onionpad.pop_mode(self)
            self.onionpad.push_mode(SelectionMode)

            return
        self.group.set_progress(progress)
        self.onionpad.schedule_display_refresh()

    def _abort(self) -> None:
        self.onionpad.set_mode(BaseMode)


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
    def encoder_actions(self) -> list:
        return [[self._encoder]]

    @property
    def keydown_actions(self) -> list:
        return [
            [lambda: None, None, None, None],
            [None, None, None, None],
            [None, None, None, None],
        ]

    @property
    def keyup_actions(self) -> list:
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
