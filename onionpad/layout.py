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

"""Components for the OLED display of the macropad."""

try:
    from typing import List, Tuple
    from collections.abc import Iterable
except ImportError as _:
    pass

import math

from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.rect import Rect
from adafruit_display_text.label import Label
from displayio import Group, OnDiskBitmap, TileGrid
from terminalio import FONT as builtinFont
from .assets import Icons


class HotkeyMap(Group):
    """A layout used to display icons for hotkeys on a 4x3 grid.

    :param positon: Horizontal and vertical position within the parent.
    """

    def __init__(
        self,
        position: Tuple[int, int],
    ):
        super().__init__(x=position[0], y=position[1])
        bitmap = OnDiskBitmap(Icons.keypad)
        self._background = TileGrid(
            bitmap,
            pixel_shader=bitmap.pixel_shader,
            x=0,
            y=0,
        )
        self.append(self._background)
        for _ in range(16):
            self.append(Group(x=0, y=0))
        self._images = [[None for _ in range(4)] for _ in range(3)]

    def set_contents(self, images: Iterable[Iterable[OnDiskBitmap]]) -> bool:
        """Update the icons for the hotkeys.

        :param images: A 2-dimensional 4x3 iterable with the images for the
                       hotkeys. Each image can either be a
                       `displayio.OnDiskBitmap` or `None`.
        :type images: typing.Iterable[typing.Iterable[~displayio.OnDiskBitmap]]
        :returns: Whether atleast one icon has changed.
        """
        changed = False
        for top, row in enumerate(images):
            for left, icon in enumerate(row):
                if self.set_icon(left, top, icon):
                    changed = True

        return changed

    def set_icon(
        self,
        left: int,
        top: int,
        icon: OnDiskBitmap | None,
    ) -> bool:
        """Update the icon at the specified position.

        :param left: The horizontal offset of the icon from the top left corner.
        :param top: The vertical offset of the icon from the top left corner.
        :param icon: The new icon or `None` to clear the current icon.
        :type icon: ~displayio.OnDiskBitmap
        :returns: Whether the new icon differs from the current icon.
        """
        if self._images[top][left] == icon:
            return False
        index = 1 + 4 * top + left
        if icon is None:
            self[index] = Group(x=0, y=0)
        else:
            self[index] = TileGrid(
                icon, pixel_shader=icon.pixel_shader, x=1 + 16 * left, y=1 + 16 * top
            )
            self._images[top][left] = icon

        return True


class LoadingCircle(Group):
    """A loading animation with a circular arc in the center of the display."""

    _POSITIONS = (
        (32, 40),
        (32, 64),
        (8, 64),
        (8, 40),
    )
    """The positions of the TileGrids of the animations on the display."""
    _STEPS = 16
    """The number of frames of the animation."""
    _STEPS_PER_TILE = 4
    """The number of frames per tile."""
    _TILES = 4
    """The number of TileGrids."""

    def __init__(self):
        super().__init__(x=0, y=0)
        self._bitmap = OnDiskBitmap(Icons.loading_circle)
        self._bitmap.pixel_shader.make_transparent(0)
        self.append(
            Circle(
                fill=0x000000,
                r=25,
                x0=32,
                y0=64,
            )
        )
        for i in range(self._TILES):
            self._add_tile(i)

    def reset(self) -> None:
        """Revert the animations to its initial state."""
        for i in range(self._TILES):
            self[i + 1].hidden = True

    def set_progress(self, progress: float) -> None:
        """Set the current progress of the animation.

        :param progress: The current progress between 0 and 1.
        """
        progress = math.ceil(self._STEPS * progress)
        full_tiles = progress // self._STEPS_PER_TILE
        partial_tile_progress = progress % self._STEPS_PER_TILE
        for i in range(self._TILES):
            if i < full_tiles:
                self[i + 1].hidden = False
                self[i + 1][0] = self._STEPS_PER_TILE - 1
            elif i == full_tiles:
                self[i + 1].hidden = False
                self[i + 1][0] = partial_tile_progress
            else:
                self[i + 1].hidden = True

    def _add_tile(self, index: int) -> None:
        """Add a new TileGrid.

        :param index: The index of the new tile between 0 and _TILES.
        """
        left, top = self._POSITIONS[index]
        self.append(
            TileGrid(
                bitmap=self._bitmap,
                pixel_shader=self._bitmap.pixel_shader,
                tile_height=24,
                tile_width=24,
                x=left,
                y=top,
            )
        )
        self._rotate_tile(index)

    def _rotate_tile(self, index: int) -> None:
        """Rotates the TileGrid with the given index into the correct position
        for the animation.

        :param index: The index of the TileGrid.
        """
        index += 1
        if index == 1:
            self[index].flip_x = False
            self[index].flip_y = False
            self[index].transpose_xy = False
        elif index == 2:
            self[index].flip_x = False
            self[index].flip_y = True
            self[index].transpose_xy = True
        elif index == 3:
            self[index].flip_x = True
            self[index].flip_y = True
            self[index].transpose_xy = False
        else:
            self[index].flip_x = True
            self[index].flip_y = False
            self[index].transpose_xy = True


class SelectionLayout(Group):
    """A simple selector to pick a single item out of several elements.

    :param positon: Horizontal and vertical position within the parent.
                    The default value aligns well with the
                    :class:`onionpad.layout.TitleLayout`.
    :param entries: The entries that are available for selection.
    :param width: The available with for the SelectionLayout.
    :param index: The index of the default item. Can be `None` to make the
                  first item the default element.
    :param max_labels: The maximum number of elements that should be displayed
                       at once.
    """

    def __init__(
        self,
        entries: List[str],
        width: int,
        position: Tuple[int, int] = (0, 12),
        max_labels: int = 7,
    ):
        super().__init__(x=position[0], y=position[1])
        self._entries = entries
        self._index = 0
        self._label_group = Group(x=0, y=0)
        self._max_labels = max_labels
        # Number of elements actually shown
        self._display_labels = min(max_labels, len(entries))
        self._init_labels(width)
        self._redraw()

    @property
    def active(self) -> str | None:
        """Access the currently selected item.

        :returns: The selected item or `None` if there are no items.
        """
        if not self._entries:
            return None
        return self._entries[self._index]

    def next(self) -> str | None:
        """Select the next item.

        :returns: The item selected after the operation.
        """
        if not self._entries:
            return None
        self._index = (self._index + 1) % len(self._entries)
        self._redraw()

        return self.active

    def previous(self) -> str | None:
        """Select the previous item.

        :returns: The item selected after the operation.
        """
        if not self._entries:
            return None
        self._index = (self._index - 1) % len(self._entries)
        self._redraw()

        return self.active

    def _init_labels(self, width: int) -> None:
        height = int(width * 1.4)
        label_height = 12
        self.append(
            Rect(
                x=0,
                y=0,
                width=width,
                height=width * 2,
                fill=0x000000,
            )
        )

        # One label would yield a negative value here, therefore the index is
        # limited to positive numbers.
        marker_index = max(self._display_labels // 2 - 1, 0)
        label_offset = height // self._max_labels
        vertical_marker_offset = marker_index * label_offset
        self.append(
            Rect(
                x=0,
                y=vertical_marker_offset,
                width=width,
                height=label_height,
                fill=0xFFFFFF,
            )
        )
        self.append(self._label_group)
        entry_count = len(self._entries)
        offset = (self._display_labels - min(entry_count, self._max_labels)) // 2
        for i in range(entry_count):
            color = 0xFFFFFF
            if i == marker_index:
                color = 0x000000
            self._label_group.append(
                Label(
                    anchor_point=(0, 0),
                    anchored_position=(2, (offset + i) * (height // self._max_labels)),
                    color=color,
                    font=builtinFont,
                    text="",
                )
            )

    def _redraw(self) -> None:
        if not self._entries:
            return
        entry_count = len(self._entries)
        elements_before_index = math.floor(self._display_labels / 2) - 1
        elements_after_index = math.ceil(self._display_labels / 2) + 1
        elements = [
            self._entries[i % entry_count]
            for i in range(
                self._index - elements_before_index,
                self._index + elements_after_index,
            )
        ]
        for i, element in enumerate(elements):
            self._label_group[i].text = element


class TitleLayout(Group):
    """Shows a short title  black on white at the top of the display.

    :param width: The width of the display.
    """

    NO_MODE = "No Mode"
    """Default title if no mode is active"""

    def __init__(self, width=int):
        super().__init__(x=0, y=0)
        self.append(
            Rect(
                x=0,
                y=0,
                width=width,
                height=12,
                fill=0xFFFFFF,
            )
        )
        self.placeholder = self.NO_MODE
        self._title = Label(
            anchor_point=(0.5, 0.0),
            anchored_position=(width // 2, 0),
            color=0x000000,
            font=builtinFont,
            text=self.placeholder,
        )
        self.append(self._title)

    @property
    def is_placeholder(self) -> bool:
        """
        :returns: Whether a title is currently set.
        """
        return self._title.text != self.placeholder

    @property
    def title(self) -> str:
        """
        :returns: The title shown on the display.
        """
        return self._title.text

    @title.setter
    def title(self, value: str | None) -> None:
        """Update the title.

        :param value: The new title or `None` for the placeholder.
        """
        if value is None:
            value = self.placeholder
        self._title.text = value
