from ctypes import *
import serial
import time

from super_map import LazyDict

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
port = setup_serial_port()

# C++ struct
class Message(Structure):
    _pack_ = 1
    _fields_ = [
        ("magic_number"    , c_uint8   ),
        ("horizontal_angle", c_float   ),
        ("vertical_angle"  , c_float   ),
        ("status"          , c_uint8   ),
    ]
message = Message(ord('a'), 0.0, 0.0, 0)

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
    should_shoot       = runtime.aiming.should_shoot
    should_look_around = runtime.aiming.should_look_around
    
    message.horizontal_angle = float(runtime.aiming.horizontal_angle)
    message.vertical_angle   = float(runtime.aiming.vertical_angle)
    message.status           = action.FIRE if should_shoot else (action.LOOK_AROUND if should_look_around else action.LOOK_AT_COORDS)
    # UP = negative (for some reason)
    # LEFT = negative
    # values are in radians
    print(f'''msg({f"{message.horizontal_angle:.4f}".rjust(7)},{f"{message.vertical_angle:.4f}".rjust(7)}, {message.status})''', end=", ")
    
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
def setup_serial_port():
    print('') # spacer
    if not serial_port:
        print('[Communication]: Port=None so no communication')
        return None # disable port
    else:
        print(f'[Communication]: Port={serial_port}')
        try:
            return serial.Serial(
                serial_port,
                baudrate=baudrate,
                timeout=config.communication.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
        except Exception as error:
            import subprocess
            # very bad hack but it works
            subprocess.run([ "bash", "-c", f"sudo -S chmod 777 '{serial_port}' <<<  \"$(cat \"$HOME/.pass\")\" ",])
            return setup_serial_port() # recursion until it works
            
def read_input():
    """
    Read data from DJI board
    :returns: received data (ended with EOL) as a string
    """
    if port is not None:
        return port.readline()