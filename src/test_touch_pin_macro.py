import gc
gc.enable()
print(gc.mem_free())
from time import monotonic
import board
import touchio
import busio
import usb_hid
from macropad import MacroHID
from connected_variables import ConnectedVariables
cv = ConnectedVariables()

# boot button


touch_pin = touchio.TouchIn(board.IO1)

# hid
while True:
    try:
        print('USB connecting')
        hid = usb_hid
        print('USB connected')
        break
    except Exception as e:
        print(e)
        pass
# define macro_hid
macro_hid = MacroHID(
    hid=hid
)

print(gc.mem_free())

cv.define('macro', "")
cv.define('status', "ready")

while True:
    if cv.read('macro'):
        try:
            cv.write('status', "waiting for touch")
            while True:
                if touch_pin.value:
                    break
            cv.write('status', "Running macro")
            macro_hid(cv.read('macro'))
            cv.write('status', "Done running macro, ready")
        except Exception as e:
            print(e)
        cv.write('macro', '')