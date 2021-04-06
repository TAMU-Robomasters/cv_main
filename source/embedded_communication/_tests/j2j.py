from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print
import serial
import time

port_param=PARAMETERS["embedded_communication"]["serial_port"]
baudrate_param=PARAMETERS["embedded_communication"]["serial_baudrate"]

connection=serial.Serial(port_param,baudrate=baudrate_param,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE)
print("Opened:",connection.name)
time.sleep(1)

connection.write(("Hello\n").encode())

print("Read:",connection.readline())

print("done")