from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print
import serial
import time
import numpy as np
import time

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

    def send_output(self,x,y,xstd,ystd,padding_per_value=5):
        """
        Send data to DJI board via serial communication as a padded string
        e.g. given x=1080, y=500, and padding_per_value=5, it will send 0108000500 to DJI board.
        :param x: x coordinate of the target. Unit: pixel. Zero coordinate: upper left
        :param y: y coordinate of the target. Unit: pixel. Zero coordinate: upper left
        """
        print("Sending To Embedded")
        x = np.uint16(int(x*10000)+32768)
        y = np.uint16(int(y*10000)+32768)

        x1 = np.uint8(x>>8)
        x2 = np.uint8(x)
        y1 = np.uint8(y>>8)
        y2 = np.uint8(y)

        # xstd = int(xstd*10)
        # ystd = int(ystd*10)
        # xstd = np.uint8(xstd) if xstd < 255 else np.uint8(255)
        # ystd = np.uint8(ystd) if ystd < 255 else np.uint8(255)

        shoot = np.uint8(1 if (xstd < 5 and ystd < 5) else 0)
        print("Shoot Value:",shoot)

        if self.port is not None:
            self.port.write("a".encode())
            self.port.write(x1.tobytes())
            self.port.write(x2.tobytes())
            self.port.write(y1.tobytes())
            self.port.write(y2.tobytes())
            self.port.write(shoot.tobytes())
            self.port.write(shoot.tobytes())
            self.port.write('e'.encode())

    def read_input(self):
        """
        Read data from DJI board
        :returns: received data (ended with EOL) as a string
        """
        if self.port is not None:
            return self.port.readline()

    def getPhi(self):
        try:
            self.port.flushInput()
            phi = self.port.read(4)[1:3]
            p1 = np.uint16(phi[0])
            p2 = np.uint16(phi[1])
            unsigned_p = ((p1 << 8) + p2)
            signed_p = np.int16((unsigned_p - 32768))/10000
            return signed_p
        except:
            # TODO: Error handling
            return None
            

embedded_communication = EmbeddedCommunication(
    port=PARAMETERS["embedded_communication"]["serial_port"],
    baudrate=PARAMETERS["embedded_communication"]["serial_baudrate"],
)