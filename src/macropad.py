# python native
from time import monotonic, sleep
# hid libs
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.mouse import Mouse
# from adafruit_hid.gamepad import Gamepad

class Limit:
    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper
    def __call__(self, val):
        if val > self.upper:
            return self.upper
        if val < self.lower:
            return self.lower
        return val
limit = Limit(-127, 127)
        
class MacroPad:
    def __init__(
        self,
        hid,
    ):
        self.keyboard = Keyboard(hid.devices)
        self.keyboard_layout = KeyboardLayoutUS(self.keyboard)
        self.consumer_control = ConsumerControl(hid.devices)
        self.mouse = Mouse(hid.devices)
        # self.gamepad = Gamepad(hid.devices)
        
        # self.gamepad_states = [0 for i in range(4)]
        
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
        # elif code.startswith('GAMEPAD_BUTTON'):
        #     n = int(code.split('_')[-1])
        #     self.gamepad.press_buttons(n)
        # elif code.startswith('JOY_ALTER'):
        #     alter = [int(axis) for axis in code.split('_')[-4:]]
        #     self.gamepad_states = [
        #         alter[i] + self.gamepad_states[i]
        #         for i in range(4)
        #     ]
        #     self.gamepad.move_joysticks(*[
        #         limit(s)
        #         for s in self.gamepad_states
        #     ])
        # elif code.startswith('JOY_SET'):
        #     self.gamepad_states = [
        #         int(axis) if int(axis) else self.gamepad_states[i]
        #         for i, axis in enumerate(code.split('_')[-4:])
        #     ]
        #     self.gamepad.move_joysticks(*[
        #         limit(s)
        #         for s in self.gamepad_states
        #     ])
        # elif code == 'JOY_CENTER':
        #     self.gamepad_states = [0, 0, 0, 0]
        #     self.gamepad.move_joysticks(*self.gamepad_states)
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
        # elif code.startswith('GAMEPAD_BUTTON'):
        #     n = int(code.split('_')[-1])
        #     self.gamepad.release_buttons(n)
        # elif code.startswith('JOY_SET'):
        #     print(self.gamepad_states)
        #     if self.n_key_press == 0:
        #         self.gamepad_states = [
        #             0 if int(axis) else self.gamepad_states[i]
        #             for i, axis in enumerate(code.split('_')[-4:])
        #         ]
        #     self.gamepad.move_joysticks(*[
        #         limit(s)
        #         for s in self.gamepad_states
        #     ])

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