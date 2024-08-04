#%% import and define
import time
from time import sleep
import board
import busio
import adafruit_mpr121

def get_raw_values(mpr121):
    return [mpr121[i].raw_value for i in range(12)]
    
init_raw_value = [147, 197, 251, 306, 306, 300, 305, 313, 149, 188, 180, 126]
threshold = 8
order = { # pin: number
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
def get_touched(mpr121):
    return [ 
        order[i]
        for i, raw in enumerate(get_raw_values(mpr121))
        if init_raw_value[i] - raw > threshold
    ]

#%% hardware
i2c = busio.I2C(board.IO6, board.IO5)
mpr121 = adafruit_mpr121.MPR121(i2c)

#%% test threshold

while False:
    print(get_raw_values(mpr121))
    sleep(1)

while False:
    for i in range(12):
        value = mpr121[i].value
        raw_value = mpr121[i].raw_value
        if value:
            print(init_raw_value[i] - raw_value)

#%% main logic
last_values = []
start = None
end = None
values = get_touched(mpr121) # initial value is not usable
while True:
    values = get_touched(mpr121)
    
    if len(last_values) == 0 and len(values) > 0:
        start = values[0]
    
    if len(last_values) > 0 and len(values) == 0:
        end = last_values[0]
    
    if end is not None:
        print([start, end])
        start = None
        end = None
    
    last_values = values