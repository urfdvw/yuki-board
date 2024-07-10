"""
MacroHID
"""
# python native
from time import monotonic, sleep
# hid libs
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.mouse import Mouse
        
class MacroHID:
    def __init__(
        self,
        hid,
    ):
        self.keyboard = Keyboard(hid.devices)
        self.keyboard_layout = KeyboardLayoutUS(self.keyboard)
        self.consumer_control = ConsumerControl(hid.devices)
        self.mouse = Mouse(hid.devices)
        
        self.cur_macro = ''

    def press_code(self, code):
        if code in Keycode.__dict__:
            self.keyboard.press(Keycode.__dict__[code])
        elif code in ConsumerControlCode.__dict__:
            self.consumer_control.press(ConsumerControlCode.__dict__[code])
        elif code in Mouse.__dict__:
            self.mouse.press(Mouse.__dict__[code])
        elif code.startswith('MOUSE_MOVE'):
            x, y, w = [int(axis) for axis in code.split('_')[-3:]]
            self.mouse.move(x=x,y=y,wheel=w)
        elif code.startswith('WAIT'):
            ms = int(code.split('_')[-1])
            sleep(ms / 1000)
        else:
            raise ValueError(
                'Bad Key Code:' + code
            )

    def release_code(self, code):
        if code in Keycode.__dict__:
            self.keyboard.release(Keycode.__dict__[code])
        elif code in ConsumerControlCode.__dict__:
            self.consumer_control.release()
        elif code in Mouse.__dict__:
            self.mouse.release(Mouse.__dict__[code])
            
    def press_hotkey(self, hotkey):
        if len(hotkey[0]) == 0:
            return
        if hotkey[0][0] == "'":
            return
        else:
            for code in hotkey:
                self.press_code(code)

    def release_hotkey(self, hotkey):
        if len(hotkey[0]) == 0:
            return
        if hotkey[0][0] == "'":
            self.keyboard_layout.write(hotkey[0][1:-1])
        else:
            for code in reversed(hotkey):
                self.release_code(code)

    def __call__(self, macro_text):
        if not macro_text:
            return
        macro = [
            [key.strip() for key in hotkey.split('|')]
            for hotkey
            in macro_text.split('~')
        ]
        self.cur_macro = macro
        print(self.cur_macro)
        for i in range(len(self.cur_macro)):
            self.press_hotkey(self.cur_macro[i])
            self.release_hotkey(self.cur_macro[i])