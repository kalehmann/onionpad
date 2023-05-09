## Onionpad

My personal code for the [Adafruit MACROPAD PR2040][adafruit_macropad].

### Example code

Lets create a hotkey for your terminal!

Asume the hotkey `Ctrl` + `Alt` + `T` opens the terminal.
Create a 14x14 pixel icon for the terminal hotkey and place it
under `icons/terminal-14.bmp` as indexed black and white (1-bit) bitmap.

Then change `code.py` to

```python
# Disable the CircuitPython console before everything else to boot seamlessly
# into the app.
# pylint: disable=wrong-import-order, wrong-import-position
from board import DISPLAY as display
display.root_group = None

from displayio import OnDiskBitmap
from onionpad import modes, Mode, OnionPad
from onionpad.hid import Keycode

class MyHotkeyMode(Mode):
    NAME="MyHotkeys"

    def __init__(self, onionpad : OnionPad):
        super().__init__(onionpad)
        self._icon OnDiskBitmap("icons/terminal-14.bmp")
        self._icon.pixel_shader.make_transparent(0)
    
     @property
    def title(self) -> str | None:
        return self.NAME

    @property
    def keydown_actions(self) -> list:
        return [
            [None, None, None, None],
            [None, None, None, None],
            [[Keycode.CTRL, Keycode.ALT, Keycode.T], None, None, None]
        ]

    @property
    def keypad_icons(self) -> None:
        return [
            [None, None, None, None],
            [None, None, None, None],
            [self._icon, None, None, None],
        ]

if __name__ == "__main__":
    app = OnionPad()
    app.set_default_mode(modes.BaseMode)
    app.register_mode(modes.HotkeyMapMode)
    app.register_mode(MyHotkeyMode)
    app.push_mode(modes.BaseMode)
    app.run()
```

### Development

The project includes a [`Makefile`][makefile] to create a bundle that can be
simply copied onto the macropad.
Building the project requires [*mpy-cross* from CircuitPython][mpy-cross].

To build the project - I.e. compile the Python files to .mpy files - simply run

```
make
```

This places the compiled Onionpad code into the `_firmware` directory.
After that execute

```
make fetch-libraries
```

to download all the required external dependencies into the `_firmware/lib`
directory.
The contents of the `_firmware` directory can then be directly copied on the
macropad.

### Api documention

The documentation built with sphinx is also
[available on the web][api_documentation].

  [adafruit_macropad]: https://www.adafruit.com/product/5100
  [api_documentation]: https://docs.kalehmann.de/onionpad/
  [makefile]: Makefile
  [mpy-cross]: https://github.com/adafruit/circuitpython/tree/main/mpy-cross 
