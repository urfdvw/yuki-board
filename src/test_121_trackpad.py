#%% import and define
import time
from time import monotonic, sleep
import board
import busio
import adafruit_mpr121


i2c = busio.I2C(board.IO6, board.IO5)
mpr121 = adafruit_mpr121.MPR121(i2c)

for i in range(12):
    mpr121[i].threshold = 5

last_values = []
start = None
end = None

position = {
    11: (0.0, 0.0),
    10: (0.0, 1.0),
    9: (0.0, 2.0),
    8: (0.0, 3.0),
    7: (1.0, 0.0),
    6: (1.0, 1.0),
    5: (1.0, 2.0),
    4: (1.0, 3.0),
    3: (2.0, 0.0),
    2: (2.0, 1.0),
    1: (2.0, 2.0),
    0: (2.0, 3.0),
}

def centered_mod(a, center, mod):
    return (a - center + 0.5 * mod) % mod + center - 0.5 * mod


class Timer:
    """
    One time use timer class
    """

    def __init__(self, hold=False):
        self.duration = 0
        self.start_time = monotonic()
        self.enable = False
        self.hold = hold
        self.dt = 0

    def over(self):
        """
        check if timer is over
        if self.hold is off
            timer is auto-reset after check
        otherwise
            timer can be checked multiple times without affectiong the result.
        """
        self.dt = monotonic() - self.start_time
        out = (self.dt > self.duration) and self.enable
        if out and not self.hold:
            self.enable = False
        return out

    def start(self, duration):
        """
        start a timer of a certian duration
        """
        self.duration = duration
        self.start_time = monotonic()
        self.enable = True

    def disable(self):
        self.enable = False


class Dict2Obj(object):
    """
    Object class that create objects from dictionary
    https://stackoverflow.com/a/1305682
    """

    def __init__(self, d):
        for k, v in d.items():
            if isinstance(k, (list, tuple)):
                setattr(self, k, [obj(x) if isinstance(x, dict) else x for x in v])
            else:
                setattr(self, k, obj(v) if isinstance(v, dict) else v)


class Relay:
    def __init__(self, thr):
        self.thr = thr
        self.remain = 0

    # on theta
    def __call__(self, x):
        self.remain += x
        if self.remain > self.thr:
            y = self.remain - self.thr
        elif self.remain < -self.thr:
            y = self.remain + self.thr
        else:
            self.remain *= 0.95
            y = 0
        self.remain = self.remain - y
        return y
        
    
class State:
    def __init__(
        self, filter_level=None, relay_thr=None, id=None
    ):
        self.id = id
        self._now = 0
        self.last = 0
        if filter_level is not None:
            self.use_filter = True
            self.alpha = 1 / 2**filter_level
        else:
            self.use_filter = False
        if relay_thr is not None:
            self.use_relay = True
            self.relay = Relay(relay_thr)
        else:
            self.use_relay = False

    @property
    def now(self):
        return self._now

    @now.setter
    def now(self, new):
        self.last = self._now
        # low pass filter
        if self.use_filter:
            new = new * self.alpha + self._now * (1 - self.alpha)
        # Relay
        diff = new - self.last
        new = self.last + (self.relay(diff) if self.use_relay else diff)
        self._now = new

    @property
    def diff(self):
        return self._now - self.last


class EventQueue:
    def __init__(self):
        self.data = []

    def append(self, given):
        self.data.append(given)

    def get(self):
        if self.data:
            return self.data.pop(0)

    def clear(self):
        self.data = []

    def __len__(self):
        return len(self.data)

    def __bool__(self):
        return bool(self.data)


class Event:
    def __init__(self, name, val):
        if name in ["press", "release", "dial", "long"]:
            self.name = name
        else:
            raise Exception("bad event ID")
        self.val = val

    def __str__(self):
        return "name: " + self.name + ", val: " + str(self.val)
        
        
class TouchBarPhysics:
    def __init__(
        self,
        pads,
        pad_max=None,
        pad_min=None,
        touch_high=True,
    ):
        # touch pads
        self.pads = pads
        self.N = len(self.pads)
        # range of touch pads
        if pad_max is None or pad_min is None:
            start_time = monotonic()
            pad_max = [0] * self.N
            pad_min = [100000] * self.N
            while monotonic() - start_time < 10:
                # run the test for 5s
                # in the mean time, slide on the ring for multiple cycles.
                for i in range(self.N):
                    sleep(0.1) # for more stable reading
                    value = self.pads[i].raw_value
                    pad_max[i] = max(pad_max[i], value)
                    pad_min[i] = min(pad_min[i], value)
                    # print(value, pad_max, pad_min )
            print(f"pad_max={pad_max},")
            print(f"pad_min={pad_min},")
            # cancel running the original script
            while True:
                pass
        else:
            if touch_high:
                self.pad_max, self.pad_min = pad_max, pad_min
            else:
                self.pad_max, self.pad_min = pad_min, pad_max
        # direction constants
        self.pos_x = [position[i][0] for i in range(self.N)]
        self.pos_y = [position[i][1] for i in range(self.N)]

        # states
        self.filter_level = 0  # not more than 2
        self.relay_thr = 0.5
        self.x = State(filter_level=self.filter_level, relay_thr=self.relay_thr)
        self.y = State(filter_level=self.filter_level, relay_thr=self.relay_thr)
        self.z = State(filter_level=self.filter_level, relay_thr=self.relay_thr)

    def get(self):
        # read sensor
        pads_now = [r.raw_value for r in self.pads]
        # conver sensor to weights
        w = [
            max(
                (pads_now[i] - self.pad_min[i]) / (self.pad_max[i] - self.pad_min[i]),
                0
            )
            for i in range(self.N)
        ]
        
        sum_w = sum(w)
        self.z.now = sum_w
        if sum_w == 0:
            self.x.now = 0
            self.y.now = 0
        else:
            tempered_weight = [(wi / sum_w) ** 2 for wi in w]
            sum_tw = sum(tempered_weight)
            if sum_tw == 0:
                self.x.now = 0
                self.y.now = 0
            else:
                tempered_weight = [twi / sum_tw for twi in tempered_weight]
                # computer weighted sum
                self.x.now = sum([tempered_weight[i] * centered_mod(self.pos_x[i], self.x.now, 3) for i in range(self.N)]) % 3
                self.y.now = sum([tempered_weight[i] * centered_mod(self.pos_y[i], self.y.now, 4) for i in range(self.N)]) % 4

        return Dict2Obj(
            {
                "x": self.x.now,
                "y": self.y.now,
                "z": self.z.now,
            }
        )

tp = TouchBarPhysics(
    pads = [mpr121[i] for i in range(12)],
    pad_max=[141, 190, 194, 157, 222, 300, 305, 303, 148, 188, 180, 127],
    pad_min=[87, 103, 94, 114, 122, 202, 152, 274, 86, 99, 86, 80],
    touch_high=False
)

touch = State()

print('startplot:', 'x', 'y')
while True:
    value = tp.get()
    if value.z > 1.5:
        touch.now = 1
        print(value.x, value.y)
    else:
        touch.now = 0
        
    if touch.diff == 1:
        print('startplot:', 'x', 'y')
        # print(int(value.x + 0.5), int(value.y + 0.5))
    # sleep(0.1)
    
