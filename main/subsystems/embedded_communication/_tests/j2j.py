from toolbox.globals import path_to, config, print
import serial
import time
import math
import numpy as np

port_param=config.embedded_communication.serial_port
baudrate_param=config.embedded_communication.serial_baudrate

connection=serial.Serial(port_param,baudrate=baudrate_param,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE)
print("Opened:",connection.name)

while True:
    x = np.uint16(int(1.23*10000)+32768)
    y = np.uint16(int(2.34*10000)+32768)

    x1 = np.uint8(x>>8)
    x2 = np.uint8(x)
    y1 = np.uint8(y>>8)
    y2 = np.uint8(y)
    shoot = np.uint8(0)
    reset_default_position = np.uint8(0)

    connection.write("a".encode())
    connection.write(x1.tobytes())
    connection.write(x2.tobytes())
    connection.write(y1.tobytes())
    connection.write(y2.tobytes())
    connection.write(shoot.tobytes())
    connection.write(reset_default_position.tobytes())
    connection.write('e'.encode())

    print("WROTE")
    time.sleep(.01)

# while True:
#     connection.flushInput()
#     phi = connection.read(4)[1:3]
#     p1 = np.uint16(phi[0])
#     p2 = np.uint16(phi[1])
#     up = ((p1 << 8) + p2)
#     sp = np.int16((up - 32768))/10000

#     print("Phi:",np.degrees(sp))
#     time.sleep(.01 )
