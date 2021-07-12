import RPi.GPIO as GPIO
 
led_pin = 12
but_pin = 18
GPIO.setmode(GPIO.BOARD)  # BOARD pin-numbering scheme
GPIO.setup(led_pin, GPIO.OUT)  # LED pin set as output
GPIO.setup(but_pin, GPIO.IN)  # Button pin set as input

# Initial state for LEDs:
GPIO.output(led_pin, GPIO.LOW)
team_color = GPIO.input(but_pin)
print("GPIO:",team_color)
GPIO.cleanup()