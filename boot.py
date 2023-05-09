import board
import digitalio
import storage
import usb_midi

# Hide CircuitPython terminal
board.DISPLAY.root_group = None
board.DISPLAY.refresh()
board.DISPLAY.auto_refresh = False

button = digitalio.DigitalInOut(board.KEY3)
button.pull = digitalio.Pull.UP

if button.value:
    storage.disable_usb_drive()
usb_midi.disable()
