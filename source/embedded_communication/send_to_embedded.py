from serial import Serial


class SendToEmbedded:
    """
    Jetson <-> DJI board communication
    """
    def __init__(self,port,baudrate):
        if port is None or port==0:
            self.port=None  # disable port
            print('Embedded Communication: Port is set to None. No communication will be established.')
        else:
            self.port=Serial(port,baudrate=baudrate,timeout=3.0)

    def send_output(self,x:int,y:int,padding_per_value=5):
        """
        Send data to DJI board via serial communication as a padded string
        e.g. given x=1080 and y=500, it will send 0108000500 to DJI board.
        :param x: x coordinate of the target. Unit: pixel. Zero coordinate: upper left
        :param y: y coordinate of the target. Unit: pixel. Zero coordinate: upper left
        """
        if self.port is not None:
            self.port.write((str(x).zfill(padding_per_value)+str(y).zfill(padding_per_value)).encode())

    def read_input(self):
        """
        Read data from DJI board
        :returns: received data (ended with EOL) as a string
        """
        if self.port is not None:
            return self.port.readline()