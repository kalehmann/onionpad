## Onionpad

My personal code for the [Adafruit MACROPAD PR2040][adafruit_macropad].

### Example code

Lets create a hotkey for your terminal!

Asume the hotkey `Ctrl` + `Alt` + `T` opens the terminal.
Create a 14x14 pixel icon for the terminal hotkey and place it
under `icons/terminal-14.bmp` as indexed black and white (1-bit) bitmap.

Then change `code.py` to

```python
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
    def keydown_events(self) -> list:
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
    app.register_mode(modes.BaseMode)
    app.register_mode(modes.HotkeyMapMode)
    app.register_mode(MyHotkeyMode)
    app.push_mode(modes.BaseMode)
    app.run()
```

  [adafruit_macropad]: https://www.adafruit.com/product/5100
