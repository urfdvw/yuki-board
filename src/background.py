"""
This script contains all classes for
Background processes
"""
from time import monotonic
from timetrigger import Repeat
from adafruit_hid.keycode import Keycode


class Background_app:
    """
    Base class for background procedures
    return 0 when not taking action
    """

    def __init__(self, freq=None, period=None):
        if freq is None and period is None:
            freq = float("inf")
        if freq is not None:
            self.freq = freq
        if period is not None:
            self.freq = 1 / period
        self.repeat_timer = Repeat(self.freq)

    def procedure(self):
        return 0

    def idle(self):
        return 0

    def __call__(self):
        if self.repeat_timer.check():
            return self.procedure()
        else:
            return self.idle()


class ScanRateMonitor(Background_app):
    """
    print the current FPS to serial
    This is used for debug propose
    """

    def __init__(self, period):
        super().__init__(period=period)
        self.start = monotonic()
        self.counter = 0

    def idle(self):
        self.counter += 1

    def procedure(self):
        if self.counter == 0:
            return 0
        now = monotonic()
        print(self.counter / (now - self.start))
        self.start = now
        self.counter = 0
        return 0


class NumLocker(Background_app):
    """
    Keep the number lock on
    Should not be used on Mac
        Will detect Mac and stop
    """

    def __init__(self, keyboard):
        super().__init__(period=0.01)
        self.keyboard = keyboard
        self.key = "key"
        self.counter = 0
        self.is_win = True

    def procedure(self):
        ## keep number lock
        if self.is_win:
            if not int.from_bytes(self.keyboard.led_status, "big") & 1:
                # if NumLock LED on
                self.keyboard.send(Keycode.KEYPAD_NUMLOCK)
                if not int.from_bytes(self.keyboard.led_status, "big") & 1:
                    # if key dose not have any effect
                    # Either NumLock is being hold
                    # or Mac
                    self.counter += 1
                    if self.counter > 50:
                        # If number raise up fastly
                        # Confirmed Mac
                        self.is_win = False
                        print("Mac detected")
                else:
                    self.counter = 0
        return 0


class MouseJitter(Background_app):
    """
    shake the cursor once a few seconds
    to keep the computer awake
    """

    def __init__(self, mouse, period):
        super().__init__(period=period)
        self.mouse = mouse

    def procedure(self):
        # Move mouse in a loop
        self.mouse.move(10, 0, 0)
        self.mouse.move(0, 10, 0)
        self.mouse.move(0, -10, 0)
        self.mouse.move(-10, 0, 0)
        return 0
