from ctypes import *
import serial
import time

from toolbox.globals import path_to, config, print, runtime

# 
# config
# 
serial_port  = config.communication.serial_port
baudrate     = config.communication.serial_baudrate

# 
# 
# initialize
# 
# 
if not serial_port:
    print('Embedded Communication: Port is set to None. No communication will be established.')
    port = None # disable port
else:
    print("Embedded Communication: Port is set to", serial_port)
    try:
        port = serial.Serial(
            serial_port,
            baudrate=baudrate,
            timeout=config.communication.timeout,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
    except Exception as error:
        import subprocess
        print("please enter password to get access to the serial port")
        subprocess.run(["sudo", "chmod", "777", serial_port, ])
        port = serial.Serial(
            serial_port,
            baudrate=baudrate,
            timeout=config.communication.timeout,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
# C++ struct
class Message(Structure):
    _pack_ = 1
    _fields_ = [
        ("magic_number"    , c_uint8   ),
        ("horizontal_angle", c_float   ),
        ("vertical_angle"  , c_float   ),
        ("should_shoot"    , c_uint8   ),
    ]
message = Message(ord('a'), 0.0, 0.0, 0)
print(f'''sizeof(message) = {sizeof(message)}''')


# 
# 
# main
# 
# 
def when_aiming_refreshes():
    message.horizontal_angle = float(runtime.aiming.horizontal_angle)
    message.vertical_angle   = float(runtime.aiming.vertical_angle)
    message.should_shoot     = int(runtime.aiming.should_shoot)
    # UP = negative (for some reason)
    # LEFT = negative
    # values are in radians
    print(f'''msg({message.horizontal_angle:.4:f},{message.vertical_angle:.4:f}, {message.should_shoot})''', end=", ")
    
    if port is not None:
        try:
            print(f'''bytes(message) = {bytes(message)}''', end=", ")
            port.write(bytes(message))
        except Exception as error:
            print("error when writing over UART")


# 
# 
# helpers
# 
# 
def read_input():
    """
    Read data from DJI board
    :returns: received data (ended with EOL) as a string
    """
    if port is not None:
        return port.readline()

def get_phi():
    """
    Read phi value sent from dev board.

    Input: None.
    Output: Value read from serial.
    """
    import numpy as np
    try:
        port.flushInput() # Get rid of data stored in buffer since UART is FIFO.
        phi = port.read(4)[1:3] # Read the first 4 bytes but only grab the middle two bytes which represent the value.

        # Combine bytes to make the full phi value
        p1 = np.uint16(phi[0])
        p2 = np.uint16(phi[1])
        unsigned_p = ((p1 << 8) + p2)
        signed_p = np.int16((unsigned_p - 32768))/10000

        return signed_p
    except:
        return None
