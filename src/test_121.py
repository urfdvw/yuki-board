#%% import and define
import time
from time import sleep
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

# while True:
#     print([mpr121[i].raw_value for i in range(12)])
while True:
    values = [
        i for i in range(12)
        if mpr121[i].value
    ]
    if len(last_values) == 0 and len(values) > 0:
        start = values[0]
    
    if len(last_values) > 0 and len(values) == 0:
        end = last_values[0]
    
    if end is not None:
        print([start, end])
        start = None
        end = None
    
    # if values != last_values:
    #     print(values)
    
    last_values = values