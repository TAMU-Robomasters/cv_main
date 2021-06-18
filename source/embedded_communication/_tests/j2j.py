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
    # x = np.uint16(int(1.23*10000)+32768)
    # y = np.uint16(int(2.34*10000)+32768)

    # x1 = np.uint8(x>>8)
    # x2 = np.uint8(x)
    # y1 = np.uint8(y>>8)
    # y2 = np.uint8(y)

    # connection.write("a".encode())
    # connection.write(x1.tobytes())
    # connection.write(x2.tobytes())
    # connection.write(y1.tobytes())
    # connection.write(y2.tobytes())
    # connection.write('e'.encode())
    # print("WROTE")
    time.sleep(.01)

    connection.flushInput()
    phee = connection.read(4)[1:3]
    p1 = np.uint16(phee[0])
    p2 = np.uint16(phee[1])
    up = ((p1 << 8) + p2)
    sp = np.int16((up - 32768))/10000

    # phee = phee
    print("Phee:",np.degrees(sp))
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
