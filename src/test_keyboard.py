#%% imports
# python native
import gc
gc.enable()
from time import monotonic

# circuit python native
import board
import busio
import usb_hid
import displayio
displayio.release_displays()

# adafruit
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# mine
from background import ScanRateMonitor
from macropad import MONO_128x32, MacroPad
from layout_macro import get_macro
from yukiswipe import YukiSwipe

#%% hardware definination
# I2C device
i2c = busio.I2C(board.IO6, board.IO5, frequency=int(1e6))

board = YukiSwipe(i2c)

#%% app definination
monitor = ScanRateMonitor(3)

#%% tests
# key input tests
while False:
    monitor()
    # read
    event = keyboard.events.get()
    if event:
        print(event)
# test macropad

while True:
    try:
        macropad = MacroPad(
            macrokeypad=keyboard,
            configure=configure,
            hid=usb_hid,
        )
        macropaddisp.show_layer(-1)
        break
    except Exception as e:
        print(e)
        pass
    


while True:
    try:
        macropad()
    except Exception as e:
        print(e)