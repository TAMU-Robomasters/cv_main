from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print
import serial
import time
import math
import numpy as np

port_param=PARAMETERS["embedded_communication"]["serial_port"]
baudrate_param=PARAMETERS["embedded_communication"]["serial_baudrate"]

connection=serial.Serial(port_param,baudrate=baudrate_param,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE)
print("Opened:",connection.name)

while True:
    connection.write(("s 00000 -0500 e ").encode(encoding="ascii"))

    time.sleep(.01)
# def convert(x,amp= 30,off = 115, b=90):
#     x = math.radians(x)
#     amp = math.radians(amp)
#     off = math.radians(off)
#     b = math.radians(b)

#     return math.sin(x*math.pi/b)*amp+off

# timerange = 5
# interval = .01
# rangeamtx = np.linspace(0,359,num=timerange/interval)

# while True:
#     for i in range(len(rangeamtx)):
#         xrad = int(math.radians(rangeamtx[i]) * 1000)
#         yrad = int(convert(rangeamtx[i]) * 1000)
#         connection.write(("s "+str(xrad).zfill(5)+" "+str(yrad).zfill(5)+" e ").encode(encoding="ascii"))
#         print(("s "+str(xrad).zfill(5)+" "+str(yrad).zfill(5)+" e "))
#         time.sleep(interval)

# print("done")
