from ctypes import *
import serial
import time

from super_map import LazyDict

from toolbox.globals import path_to, config, print, runtime
from subsystems.communicating.serial_help import setup_serial_port

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
port = setup_serial_port()

# C++ struct
class Message(Structure):
    _pack_ = 1
    _fields_ = [
        ("magic_number"    , c_uint8   ),
        ("horizontal_angle", c_float   ),
        ("vertical_angle"  , c_float   ),
        ("depth"           , c_float   ),
        ("status"          , c_uint8   ),
    ]
message = Message(ord('a'), 0.0, 0.0, 0.0, 0)

action = LazyDict(
    LOOK_AROUND=0,
    LOOK_AT_COORDS=1,
    FIRE=2,
)

# 
# 
# main
# 
# 
def when_aiming_refreshes():
    global port
    should_shoot       = runtime.aiming.should_shoot
    should_look_around = runtime.aiming.should_look_around
    
    message.horizontal_angle = float(runtime.aiming.horizontal_angle)
    message.vertical_angle   = float(runtime.aiming.vertical_angle)
    message.depth            = float(runtime.aiming.depth_amount)
    message.status           = action.FIRE if should_shoot else (action.LOOK_AROUND if should_look_around else action.LOOK_AT_COORDS)
    # UP = negative (for sentry because technically the sentry's camera is upsidedown)
    # LEFT = negative
    # values are in radians
    print(f'''msg({f"horizontal:{message.horizontal_angle:.4f}".rjust(7)},{f"vertical:{message.vertical_angle:.4f}".rjust(7)},{f"depth:{message.depth:.2f}".rjust(7)}, {message.status})''', end=", ")
    
    try:
        port.write(bytes(message))
    except Exception as error:
        print(f"\n[Communication]: error when writing over UART: {error}")
        port = setup_serial_port() # attempt re-setup

# overwrite function if port is None
if port is None:
    def when_aiming_refreshes():
        pass # do nothing intentionally

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