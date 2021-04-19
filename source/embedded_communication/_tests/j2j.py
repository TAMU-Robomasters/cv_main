from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print
import serial
import time
import math
import numpy as np

port_param=PARAMETERS["embedded_communication"]["serial_port"]
baudrate_param=PARAMETERS["embedded_communication"]["serial_baudrate"]

connection=serial.Serial(port_param,baudrate=baudrate_param,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE)
print("Opened:",connection.name)

timerange = 5
interval = .01
rangeamtx = np.linspace(80,90,num=timerange/interval)
rangeamty = np.linspace(250,270,num=timerange/interval)


while True:
    for i in range(len(rangeamtx)):
        xrad = int(math.radians(rangeamtx[i]) * 1000)
        yrad = int(math.radians(rangeamty[i]) * 1000)
        connection.write(("s "+str(xrad).zfill(5)+" "+str(yrad).zfill(5)+" e ").encode(encoding="ascii"))
        time.sleep(interval)

    for i in range(len(rangeamtx)):
        if i == 0:
            continue
        xrad = int(math.radians(rangeamtx[-i]) * 1000)
        yrad = int(math.radians(rangeamty[-i]) * 1000)
        connection.write(("s "+str(xrad).zfill(5)+" "+str(yrad).zfill(5)+" e ").encode(encoding="ascii"))
        time.sleep(interval)
    print("completed iteration")

print("done")
