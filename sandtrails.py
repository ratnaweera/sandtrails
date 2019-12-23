from time import sleep
import RPi.GPIO as GPIO
import curses

TH_DIR = 5   # Direction GPIO Pin
TH_STEP = 6  # Step GPIO Pin
TH_MODE = (26, 19, 13)   # Microstep Resolution GPIO Pins

RH_DIR = 21   # Direction GPIO Pin
RH_STEP = 20  # Step GPIO Pin
RH_MODE = (22, 27, 17)   # Microstep Resolution GPIO Pins

CW = 1     # Clockwise Rotation
CCW = 0    # Counterclockwise Rotation
SPR = 200   # Steps per Revolution

GPIO.setmode(GPIO.BCM)
GPIO.setup(TH_DIR, GPIO.OUT)
GPIO.setup(TH_STEP, GPIO.OUT)
GPIO.setup(RH_DIR, GPIO.OUT)
GPIO.setup(RH_STEP, GPIO.OUT)
GPIO.output(TH_DIR, CW)
GPIO.output(RH_DIR, CW)

GPIO.setup(TH_MODE, GPIO.OUT)
GPIO.setup(RH_MODE, GPIO.OUT)
RESOLUTION = {'Full': (0, 0, 0),
              'Half': (1, 0, 0),
              '1/4': (0, 1, 0),
              '1/8': (1, 1, 0),
              '1/16': (0, 0, 1),
              '1/32': (1, 0, 1)}
GPIO.output(RH_MODE, RESOLUTION['1/32'])
GPIO.output(TH_MODE, RESOLUTION['1/32'])

#step_count = SPR * 32
step_count = SPR / 10
delay = .002 / 32

# Set up curses
screen = curses.initscr() # get the curses screen window
curses.noecho() # turn off input echoing
curses.cbreak() # respond to keys immediately (don't wait for enter)
screen.keypad(True) # map arrow keys to special values



try:
    screen.addstr(0, 0, 'Press q to quit')
    while True:
        char = screen.getch()
        if char == ord('q'):
            break
        elif char == curses.KEY_RIGHT:
            for x in range(step_count):
                GPIO.output(TH_DIR, CW)
                GPIO.output(TH_STEP, GPIO.HIGH)
                sleep(delay)
                GPIO.output(TH_STEP, GPIO.LOW)
                sleep(delay)
        elif char == curses.KEY_LEFT:
            for x in range(step_count):
                GPIO.output(TH_DIR, CCW)
                GPIO.output(TH_STEP, GPIO.HIGH)
                sleep(delay)
                GPIO.output(TH_STEP, GPIO.LOW)
                sleep(delay)       
        elif char == curses.KEY_UP:
            for x in range(step_count):
                GPIO.output(RH_DIR, CW)
                GPIO.output(RH_STEP, GPIO.HIGH)
                sleep(delay)
                GPIO.output(RH_STEP, GPIO.LOW)
                sleep(delay)              
        elif char == curses.KEY_DOWN:
            for x in range(step_count):
                GPIO.output(RH_DIR, CCW)
                GPIO.output(RH_STEP, GPIO.HIGH)
                sleep(delay)
                GPIO.output(RH_STEP, GPIO.LOW)
                sleep(delay)
        
        
finally:
    # shut down cleanly
    curses.nocbreak(); screen.keypad(0); curses.echo()
    curses.endwin()
    GPIO.cleanup()

