import serial
import time


port = serial.Serial(
    "/dev/ttyTHS0",
    baudrate=115200,
    timeout=.05,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE
)


while 1:
    print(f'''----------------------------------------''')
    print(f'''Writing 1''')
    port.write(bytes("1\n\0", 'ascii'))
    time.sleep(5)
    
    print(f'''Reading''')
    result = port.readline()
    print(f'''result = {result}''')
    time.sleep(5)
    
    
    