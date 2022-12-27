from toolbox.globals import path_to, config, print, runtime
import serial

serial_port  = config.communication.serial_port
baudrate     = config.communication.serial_baudrate

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
