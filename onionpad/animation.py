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

"""Animations for the OLED display of the macropad."""

import math
from displayio import Group, OnDiskBitmap, TileGrid
from adafruit_display_shapes.circle import Circle

from .assets import Icons


class Animation(Group):
    """Base class for animations on the OLED display."""

    # pylint: disable-next=unused-argument
    def update(self, progress: float) -> bool:
        """Updates the animation to the given progress.

        :param progress: The progress of the animation between 0 and 1
        :returns: Whether the animation has changed and the display should
                  be refreshed.
        """
        return False


class LoadingCircle(Animation):
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

    def __init__(self) -> None:
        super().__init__(x=0, y=0)
        self._bitmap = Icons.loading_circle()
        self._tiles: list[TileGrid] = []
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

    def update(self, progress: float) -> bool:
        """Set the current progress of the animation.

        :param progress: The current progress between 0 and 1.
        """
        change = False
        progress = math.ceil(self._STEPS * progress)
        full_tiles = progress // self._STEPS_PER_TILE
        partial_tile_progress = progress % self._STEPS_PER_TILE
        for i in range(self._TILES):
            if i < full_tiles:
                if self._tiles[i].hidden:
                    change = True
                self._tiles[i].hidden = False
                if self._tiles[i][0] != self._STEPS_PER_TILE - 1:
                    change = True
                self._tiles[i][0] = self._STEPS_PER_TILE - 1
            elif i == full_tiles:
                if self._tiles[i].hidden:
                    change = True
                self._tiles[i].hidden = False
                self._tiles[i][0] = partial_tile_progress
                if self._tiles[i][0] != partial_tile_progress:
                    change = True
            else:
                if not self._tiles[i].hidden:
                    change = True
                self._tiles[i].hidden = True

        return change

    def _add_tile(self, index: int) -> None:
        """Add a new TileGrid.

        :param index: The index of the new tile between 0 and _TILES.
        """
        left, top = self._POSITIONS[index]
        tile = TileGrid(
            bitmap=self._bitmap,
            pixel_shader=self._bitmap.pixel_shader,
            tile_height=24,
            tile_width=24,
            x=left,
            y=top,
        )
        self.append(tile)
        self._tiles.append(tile)
        self._rotate_tile(index)

    def _rotate_tile(self, index: int) -> None:
        """Rotates the TileGrid with the given index into the correct position
        for the animation.

        :param index: The index of the TileGrid.
        """
        if index == 0:
            self._tiles[index].flip_x = False
            self._tiles[index].flip_y = False
            self._tiles[index].transpose_xy = False
        elif index == 1:
            self._tiles[index].flip_x = False
            self._tiles[index].flip_y = True
            self._tiles[index].transpose_xy = True
        elif index == 2:
            self._tiles[index].flip_x = True
            self._tiles[index].flip_y = True
            self._tiles[index].transpose_xy = False
        else:
            self._tiles[index].flip_x = True
            self._tiles[index].flip_y = False
            self._tiles[index].transpose_xy = True


class TileAnimation(Animation):
    """
    :param position:
    :param source:
    :param tile_size:
    """

    def __init__(
        self,
        position: tuple[int, int],
        source: OnDiskBitmap,
        tile_size: tuple[int, int],
    ) -> None:
        super().__init__(x=position[0], y=position[1])
        self._tile_grid = TileGrid(
            bitmap=source,
            pixel_shader=source.pixel_shader,
            x=0,
            y=0,
            width=1,
            height=1,
            tile_width=tile_size[0],
            tile_height=tile_size[1],
        )
        self.append(self._tile_grid)
        columns = source.width // tile_size[0]
        rows = source.height // tile_size[1]
        self._frames = columns * rows

    def update(self, progress: float) -> bool:
        """
        :param progress:
        :returns:
        """
        new_frame = int(self._frames * progress)
        changed = self._tile_grid[0] != new_frame
        self._tile_grid[0] = new_frame

        return changed
