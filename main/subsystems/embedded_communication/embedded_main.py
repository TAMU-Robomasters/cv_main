from toolbox.globals import MACHINE, PATHS, PARAMETERS, print
import serial
import time
import numpy as np
import time

import subsystems.integration.integration_methods as integration_methods
from subsystems.integration.import_parameters import *

class EmbeddedCommunication:
    """
    Jetson <-> DJI board communication
    """
    def __init__(self, port, baudrate):
        if not port:
            self.port = None # disable port
            print('Embedded Communication: Port is set to None. No communication will be established.')
        else:
            print("Embedded Communication: Port is set to", port)
            self.port=serial.Serial(
                port,
                baudrate=baudrate,
                timeout=.05,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )

    def send_output(self,x,y,shoot,reset_default_position=0):
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
        
        # print(" reset_position:", reset_default_position)
        # print(" shoot:", shoot)

        if self.port is not None:
            self.port.write("a".encode())
            self.port.write(x1.tobytes())
            self.port.write(x2.tobytes())
            self.port.write(y1.tobytes())
            self.port.write(y2.tobytes())
            self.port.write(shoot.tobytes())
            self.port.write(reset_default_position.tobytes())
            self.port.write('e'.encode())

        return shoot

    def read_input(self):
        """
        Read data from DJI board
        :returns: received data (ended with EOL) as a string
        """
        if self.port is not None:
            return self.port.readline()

    def get_phi(self):
        """
        Read phi value sent from dev board.

        Input: None.
        Output: Value read from serial.
        """
        try:
            self.port.flushInput() # Get rid of data stored in buffer since UART is FIFO.
            phi = self.port.read(4)[1:3] # Read the first 4 bytes but only grab the middle two bytes which represent the value.

            # Combine bytes to make the full phi value
            p1 = np.uint16(phi[0])
            p2 = np.uint16(phi[1])
            unsigned_p = ((p1 << 8) + p2)
            signed_p = np.int16((unsigned_p - 32768))/10000

            return signed_p
        except:
            return None

    def send_embedded_command(self, found_robot, horizontal_angle, vertical_angle, depth_amount, x_circular_buffer, y_circular_buffer, x_std, y_std):
        """
        Tell embedded where to shoot and whether or not to shoot.

        Input: If a robot was detected, the angles to turn by, the depth, the circular buffers for x and y, and how locked on we are.
        Output: None.
        """

        if found_robot:
            # Send embedded the angles to turn to and the accuracy, make accuracy terrible if we dont have enough data in buffer 
            if depth_amount < min_range or depth_amount > max_range:
                x_circular_buffer.clear()
                y_circular_buffer.clear()
                shoot = self.send_output(horizontal_angle, vertical_angle, 0)
            elif len(x_circular_buffer) == std_buffer_size:
                send_shoot_val = integration_methods.send_shoot(x_std,y_std)
                shoot = self.send_output(horizontal_angle, vertical_angle,send_shoot_val)
            else:
                shoot = self.send_output(horizontal_angle, vertical_angle, 0)
        else:
            # Clears buffers since no robots detected
            x_circular_buffer.clear()
            y_circular_buffer.clear()
            embedded_communication.send_output(0, 0, 0) # Tell embedded to stay still 
            print(" bounding_boxes: []")
            

embedded_communication = EmbeddedCommunication(
    port=PARAMETERS["embedded_communication"]["serial_port"],
    baudrate=PARAMETERS["embedded_communication"]["serial_baudrate"],
)