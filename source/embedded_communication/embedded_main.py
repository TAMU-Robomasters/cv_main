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
        if port is None or port==0:
            self.port=None  # disable port
            print('Embedded Communication: Port is set to None. No communication will be established.')
        else:
            print("Embedded Communication: Port is set to",port)
            self.port=serial.Serial(port,baudrate=baudrate,timeout=3.0,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE)

    def send_output(self,x,y,t1,padding_per_value=5):
        """
        Send data to DJI board via serial communication as a padded string
        e.g. given x=1080, y=500, and padding_per_value=5, it will send 0108000500 to DJI board.
        :param x: x coordinate of the target. Unit: pixel. Zero coordinate: upper left
        :param y: y coordinate of the target. Unit: pixel. Zero coordinate: upper left
        """
        modelTime = 0
        print("Sending To Embedded")
        x = np.uint16(int(x*10000)+32768)
        y = np.uint16(int(y*10000)+32768)

        x1 = np.uint8(x>>8)
        x2 = np.uint8(x)
        y1 = np.uint8(y>>8)
        y2 = np.uint8(y)

        # if self.port is not None:
        #     self.port.write("a".encode())
        #     self.port.write(x1.tobytes())
        #     self.port.write(x2.tobytes())
        #     self.port.write(y1.tobytes())
        #     self.port.write(y2.tobytes())
        #     self.port.write('e'.encode())
        #     modelTime = time.time()-t1
        self.port.write("s_blah_e".encode())
        if PARAMETERS['testing']['debugging_use_round_trip_timing']:
            while True:
                output = self.port.readline()
                try:
                    output = str(output)
                    if output[-4] + output[-3] + output[-2] + output[-1] != "abc\n":
                        print('incoming message:', output)
                        self.port.write("s_blah_e".encode())
                except:
                    pass
                
            
        return modelTime
            # self.port.write(("s "+str(x).zfill(padding_per_value)+" "+str(y).zfill(padding_per_value)+" e ").encode())
        # print(("s "+str(x).zfill(padding_per_value)+" "+str(y).zfill(padding_per_value)+" e "))

    def read_input(self):
        """
        Read data from DJI board
        :returns: received data (ended with EOL) as a string
        """
        if self.port is not None:
            return self.port.readline()

embedded_communication = EmbeddedCommunication(
    port=PARAMETERS["embedded_communication"]["serial_port"],
    baudrate=PARAMETERS["embedded_communication"]["serial_baudrate"],
)