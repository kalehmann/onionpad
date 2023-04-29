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

"""Provides easy access to the path of the icons of the project."""

import os

from .util import dirname


class _FileFinder:  # pylint: disable=too-few-public-methods
    """Obtain the file path of assets from the attributes of this class.

    :param basepath: The path prepended to an attribute name. This is usually a
                     folder.
    :param postfix: This is appended after the attribute name. Usually a file
                    extension.
    :param subfinders: Other _FileFinders that can be accessed as attributes.
                       The keys are the names of the attributes.

    Examples::

        print(os.listdir("icons/")) # ["test.bmp"]
        icons = _FileFinder("icons", ".bmp")
        print(icons.test) # "icons/test.bmp"
    """

    def __init__(
        self,
        basepath: str,
        postfix: str,
        subfinders: dict | None = None,
    ):
        if not basepath.endswith(os.sep):
            basepath += os.sep
        self._basepath = basepath
        self._postfix = postfix
        if subfinders is None:
            subfinders = {}
        self._subfinders = subfinders

    def __getattr__(self, name: str) -> str | "_FileFinder":
        if name in self._subfinders:
            return self._subfinders[name]
        path = self._basepath + name + self._postfix
        try:
            os.stat(path)
        except OSError as exception:
            raise AttributeError(
                f"No attribute `{name}`. File '{path}' does not exist"
            ) from exception

        return path


_icons_directory = dirname(__file__) + os.sep + "icons/"
Icons = _FileFinder(
    _icons_directory,
    ".bmp",
    {
        "generic": _FileFinder(
            _icons_directory + "generic/",
            "-14.bmp",
        ),
    },
)
