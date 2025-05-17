# python native
from time import monotonic, sleep
# hardware libs
import keypad
# hid libs
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.mouse import Mouse
# layout
from layout_macro import get_macro

class EventQueue:
    def __init__(self):
        self.data = []

    def append(self, given):
        self.data.append(given)

    def get(self):
        if self.data:
            return self.data.pop(0)
        else:
            return None

    def clear(self):
        self.data = []

    def __len__(self):
        return len(self.data)

    def __bool__(self):
        return bool(self.data)

class MacroTouchPad:
    def __init__(self):
        # queue
        self._events = EventQueue()
        
    def addEvents(self, start, end):
        macro = get_macro(start, end)
        self._events.append(macro)

    @property
    def events(self):
        position = self.encoder.position
        if position != 0:
            key_number = self.n_keys if position > 0 else self.n_keys + 1
            position = abs(position)
            for i in range(position):
                self._events.append(
                    keypad.Event(
                        key_number=key_number,
                        pressed=True,
                    )
                )
                self._events.append(
                    keypad.Event(
                        key_number=key_number,
                        pressed=False,
                    )
                )
            self.encoder.position = 0
            
        return self._events

class MacroPadDisplay:
    def __init__(self, display):
        self.display = display
        self.splash = displayio.Group()
        self.display.show(self.splash)

        self.layer_group = displayio.Group()
        self.splash.append(self.layer_group)
        self.layer_group.hidden = False
        self.layer_lable = Label(
            FONT,
            text='',
        )
        self.layer_group.append(self.layer_lable)

        self.macro_group = displayio.Group()
        self.splash.append(self.macro_group)
        self.macro_group.hidden = True
        self.macro_lable = Label(
            FONT,
            text='',
            scale=2,
        )
        self.macro_group.append(self.macro_lable)

        self.layer = -1
        self.state = 0

    def show_layer_text(self, text):
        if (self.layer_lable.text == text
        and self.state == 0):
            return
        self.state = 0
        self.layer_lable.text = text
        self.layer_group.hidden = False
        self.macro_group.hidden = True

    def show_macro_text(self, text):
        if (self.macro_lable.text == text
        and self.state == 1):
            return
        self.state = 1
        self.macro_lable.text = text
        self.layer_group.hidden = True
        self.macro_group.hidden = False


class MONO_128x32(MacroPadDisplay):
    # need to change
    def __init__(self, configure, display):
        super().__init__(display)
        self.configure = configure.configure
        self.layer_text = {
            layer: '\n'.join(wrap_text_to_lines(
                ' '.join([
                    str(key_number) + ':' + self.configure[layer][key_number][0]
                    for key_number in sorted(self.configure[layer].keys())
                    if self.configure[layer][key_number][0]
                ])
            , 128 // 6))
            for layer in self.configure
        }
        # print(self.layer_text)

        self.layer_lable.color=0xFFFFFF
        self.layer_lable.background_color=0x000000
        self.layer_lable.x=0
        self.layer_lable.y=5
        self.layer_lable.line_spacing=0.8

        self.macro_lable.color=0xFFFFFF
        self.macro_lable.background_color=0x000000
        self.macro_lable.x=0
        self.macro_lable.y=15
        
        self.show_layer(-1)

    def show_layer(self, layer):
        self.layer = layer
        text = self.layer_text[layer]
        self.show_layer_text(text)

    def show_macro(self, key_number):
        text = self.configure[self.layer][key_number][0]
        self.show_macro_text(text)
        
class MacroPad:
    def __init__(
        self,
        macrokeypad,
        hid,
        macropaddisp=None,
    ):
        self.macrokeypad = macrokeypad
        self.macropaddisp = macropaddisp

        self.layer = -1
        self.n_layer_key_press = 0
        self.n_key_press = 0

        self.keyboard = Keyboard(hid.devices)
        self.keyboard_layout = KeyboardLayoutUS(self.keyboard)
        self.consumer_control = ConsumerControl(hid.devices)
        self.mouse = Mouse(hid.devices)
        
        self.cur_macro = ''

        if self.macropaddisp:
            self.start_time = monotonic()
            self.CD = 1
            self.displaying_macro = False

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

    def __call__(self):
        # reset layer screen
        if self.macropaddisp and self.displaying_macro:
            if (monotonic() - self.start_time > self.CD
            and self.n_key_press == 0):
                self.macropaddisp.show_layer(self.layer)
                self.displaying_macro = False
        # get event
        macro = self.macrokeypad.events.get()
        if macro is None or macro == "":
            return
        # get layer
            self.cur_macro = macro
            
            # print(self.cur_macro)
            
            # press
            for i in range(len(self.cur_macro)):
                self.press_hotkey(self.cur_macro[i])
                if i != len(self.cur_macro) - 1:
                    self.release_hotkey(self.cur_macro[i])
            if self.macropaddisp:
                self.macropaddisp.show_macro(event.key_number)
                self.displaying_macro = True
                self.start_time = monotonic()
            # release
            self.release_hotkey(self.cur_macro[-1])
