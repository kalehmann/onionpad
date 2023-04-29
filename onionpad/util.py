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

"""Helper classes and function for the OnionPad"""

from collections import OrderedDict
import os


class LayeredMap:
    """A 2-dimensional structure with multiple layers.

    Element access traverses trough the layers from top to bottom and returns
    the first element different from `None`, that is found in a layer at the
    requested position.

    :param width: The number of elements per row.
    :param height: The number of rows.

    Examples::

        l = LayeredMap(2, 2)
        print(l[0][0]) # None
        l.push_layer([[1, None], [None, 2]], "foo")
        l.push_layer([[None, 3], [None, 4]], "bar")
        print(l[1][0]) # None
        print(l[1][1]) # 4
        l.remove_layer("bar")
        print(l[1][1]) # 2
    """

    def __init__(self, width: int, height: int):
        self._height = height
        self._width = width
        self._layers = OrderedDict()

    @property
    def width(self) -> int:
        """
        :returns: The number of columns in the layered map.
        """
        return self._width

    @property
    def height(self) -> int:
        """
        :returns: The number of rows in the layered map.
        """
        return self._height

    @property
    def immutable(self) -> tuple:
        """
        :returns: A tuple of the contents.
        """
        return tuple(tuple(element for element in row) for row in self)

    def push_layer(self, layer: list, name: str) -> None:
        """Adds a new layer on top of the map.

        :param layer: A 2-dimensional list with equal dimensions to the
                      LayeredMap.
        :param name: The name of the new layer.
        """
        if len(layer) != self.height:
            raise ValueError(
                "The height of the layer does not match the height of the " "LayeredMap"
            )
        for i, row in enumerate(layer):
            if len(row) != self.width:
                raise ValueError(
                    f"The width of row {i} of the layer does not match the "
                    "width of the LayeredMap"
                )
        self._layers[name] = layer

    def remove_layer(self, name: str) -> None:
        """Removes a layer from the map.

        :param name: The name of the layer.
        """
        self._layers.pop(name)

    def __getitem__(self, key: int) -> tuple:
        if not 0 <= key < self.height:
            raise IndexError()
        row = [None for _ in range(self.width)]
        layers = list(self._layers.values())
        for layer in reversed(layers):
            for i, item in enumerate(layer[key]):
                if item is not None and row[i] is None:
                    row[i] = item
        return tuple(row)

    def __len__(self) -> int:
        return self.height

    def __iter__(self):
        return (self[i] for i in range(self.height))


def dirname(path: str) -> str:
    """Extracts the directory component from a path.

    :param path: The path
    :returns: The directory component of the path.
    """
    index = path.rfind(os.sep) + 1
    if index < 0:
        return path
    directory = path[:index]
    if directory == os.sep * len(directory):
        return directory
    return directory.rstrip(os.sep)


def hsv_to_rgb(hue: float, saturation: float, value: float) -> tuple:
    """Convert a color from the HSV to the RGB model.

    :param hue: The hue of the color between 0 and 1.
    :param saturation: The saturation of the color between 0 and 1.
    :param value: The value of the color between 0 and 1.
    :returns: The red, green and blue value of the color. All returned values
              are located between 0 and 1.
    """
    # See https://en.wikipedia.org/wiki/HSL_and_HSV#HSV_to_RGB
    root_color = hue * 6.0
    chroma = value * saturation
    base = value - chroma
    supplement = chroma * (1 - abs(root_color % 2 - 1))
    root_color = int(root_color)
    if root_color == 0:
        return (chroma + base, supplement + base, base)
    if root_color == 1:
        return (supplement + base, chroma + base, base)
    if root_color == 2:
        return (base, chroma + base, supplement + base)
    if root_color == 3:
        return (base, supplement + base, chroma + base)
    if root_color == 4:
        return (supplement + base, base, chroma + base)
    return (chroma + base, base, supplement + base)


def pack_rgb(red: float, green: float, blue: float) -> int:
    """Pack an RGB color into a 3-byte integer.

    Examples::

        print(hex(pack_rgb(1, 1, 1))) # 0xFFFFFF
        print(hex(pack_rgb(1, 0, 0))) # 0xFF0000

    :param red: The red component between 0 and 1.
    :param green: The green component between 0 and 1.
    :param blue: The blue component between 0 and 1.
    :returns: The color as integer between 0 and 0xFFFFFF
    """
    return (int(0xFF * red) << 16) + (int(0xFF * green) << 8) + int(0xFF * blue)


def hsv_to_packed_rgb(hue: float, saturation: float, value: float) -> int:
    """Convert a color from the HSV model to a packed 3-byte RGB integer.

    :param hue: The hue of the color between 0 and 1.
    :param saturation: The saturation of the color between 0 and 1.
    :param value: The value of the color between 0 and 1.
    :returns: The color as integer between 0 and 0xFFFFFF
    """
    return pack_rgb(*hsv_to_rgb(hue, saturation, value))
