import serial
import time
# 
# Xavier3
# 

from ctypes import *

class Message(Structure):
    _pack_ = 1
    _fields_ = [
        ("magic_number"    , c_uint8  ),
        ("horizontal_angle", c_float   ),
        ("vertical_angle"  , c_float   ),
        ("should_shoot"    , c_uint8   ),
    ]
message = Message(ord('a'), 0.0, 0.0, 0)

port = serial.Serial(
    "/dev/ttyTHS0",
    baudrate=115200,
    timeout=5.5,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE
)

inc = 0
while 1:
    try:
        #print(f'''----------------------------------------''')
        #print(f'''Writing {bytes(message)}''')
        # print(f'''sizeof(message) = {sizeof(message)}''')
        inc += 1
        #print(f'''inc = {inc}''')
        # for each in bytes(message):
        #     print(int(each))
        message.horizontal_angle += 1
        port.write(bytes(message))
        #port.write("a".encode())
        #print(f'''port.out_waiting = {port.out_waiting}''')
        time.sleep(0.02)
        
        # print(f'''Reading''')
        # # result = port.readline()
        # print(f'''result = {result}''')
        # time.sleep(1)
        
        
    except Exception as error:
        print(f'''error = {error}''')
    
