#%% import and define
import time
from time import sleep
import board
import busio
import adafruit_mpr121

class YukiSwipe:
    def __init__(self, i2c):
        # config
        self.threshold = 8
        self.order = { # pin: number
            11: 1,
            7: 2,
            3: 3,
            10: 4,
            6: 5,
            2: 6,
            9: 7,
            5: 8,
            1: 9,
            8: 10,
            4: 11,
            0: 12
        }
        # hardware
        self.mpr121 = adafruit_mpr121.MPR121(i2c)
        for i in range(10):
            self.init_raw_value = self.get_raw_values()
            sleep(0.1)
        print("done initializing")
        # states
        self.last_values = ()
        self.start = None
        self.end = None
        
    def get_raw_values(self):
        return tuple(self.mpr121[i].raw_value for i in range(12))
        
    def get_touched(self):
        return tuple(
            self.order[i]
            for i, raw in enumerate(self.get_raw_values())
            if self.init_raw_value[i] - raw > self.threshold
        )
        
    def __call__(self):
        out = None # placeholder
        
        self.values = self.get_touched()
    
        if len(self.last_values) == 0 and len(self.values) > 0:
            self.start = self.values[0]
        
        if len(self.last_values) > 0 and len(self.values) == 0:
            self.end = self.last_values[0]
        
        if self.end is not None:
            out = (self.start, self.end)
            self.start = None
            self.end = None
            
        
        self.last_values = self.values
        return out
        
# #%% test
# i2c = busio.I2C(board.IO6, board.IO5)
# board = YukiSwipe(i2c)
# while True:
#     swipe = board()
#     if swipe is not None:
#         print(swipe)