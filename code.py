# Disable the CircuitPython console before everything else to boot seamlessly
# into the app.
# pylint: disable=wrong-import-order, wrong-import-position
from board import DISPLAY as display
display.root_group = None

from onionpad import modes, OnionPad

if __name__ == "__main__":
    app = OnionPad()
    app.set_default_mode(modes.BaseMode)
    app.register_mode(modes.AmbientMode)
    app.register_mode(modes.HotkeyMapMode)
    app.register_mode(modes.MediaMode)
    app.run()
