import serial
import time
import numpy as np
import time

from toolbox.globals import path_to, config, print, runtime

# 
# config
# 
serial_port = config.embedded_communication.serial_port
baudrate    = config.embedded_communication.serial_baudrate

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
    port = serial.Serial(
        serial_port,
        baudrate=baudrate,
        timeout=.05,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE
    )


# 
# 
# main
# 
# 
def when_aiming_refreshes():
    # yup thats all there is to it
    send_output(
        x=runtime.aiming.horizontal_angle,
        y=runtime.aiming.vertical_angle,
        shoot=runtime.aiming.should_shoot,
    )


# 
# 
# helpers
# 
# 
def send_output(x, y, shoot, reset_default_position=0):
    """
    Send data to DJI board via serial communication as raw bytes.

    Input: Data to send which can be written as bytes.
    Output: None.
    """

    # Convert all data to constrained bytes.
    x = np.uint16(int(x*10000)+32768)
    y = np.uint16(int(y*10000)+32768)

    x1 = np.uint8(x>>8)
    x2 = np.uint8(x)
    y1 = np.uint8(y>>8)
    y2 = np.uint8(y)

    reset_default_position = np.uint8(reset_default_position)
    shoot = np.uint8(shoot)
    
    print(" reset_position:", reset_default_position, end=", ")
    print(" shoot:", shoot, end=", ")

    if port is not None:
        port.write("a".encode())
        port.write(x1.tobytes())
        port.write(x2.tobytes())
        port.write(y1.tobytes())
        port.write(y2.tobytes())
        port.write(shoot.tobytes())
        port.write(reset_default_position.tobytes())
        port.write('e'.encode())

    return shoot

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
