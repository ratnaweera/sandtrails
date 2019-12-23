from time import sleep
from math import pi
import RPi.GPIO as GPIO

TH_DIR = 5   # Direction GPIO Pin
TH_STEP = 6  # Step GPIO Pin
TH_MODE = (26, 19, 13)   # Microstep Resolution GPIO Pins

RH_DIR = 21   # Direction GPIO Pin
RH_STEP = 20  # Step GPIO Pin
RH_MODE = (22, 27, 17)   # Microstep Resolution GPIO Pins

CW = 1      # Clockwise Rotation
CCW = 0     # Counterclockwise Rotation
SPR = 200*32   # Steps per Revolution
DRHO = 14   # Diameter spur gear of Rho axis [mm]
AXISTYPE = {
    'Rho': 0,
    'Theta': 1}
delay = 0.006 / 32

def setup_steppermotors():
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

    
class axis:
    def __init__(self, axistype, llimit, ulimit):
        self.axistype = axistype
        self.llimit = llimit
        self.ulimit = ulimit
        self.curSteps = 0
        self.curPos = 0
        self.tarSteps = 0
        self.tarPos = 0
        self.homed = False
    
    def printState(self):
        print("(" + str(self.curSteps) + ", " + str(self.curPos) + ", " + str(self.tarSteps) + ", " + str(self.tarPos) + ") ( curSteps, curPos, tarSteps, tarPos)")
        
    def homing(self):
        # Drive until we see the sensor, depends on type
        self.curSteps = self.curPos = 0
        self.homed = True
        
    def goTo(self, dest):
        if not self.homed:
            print("Not homed!")
            return -1
        elif (dest < self.llimit) or (dest > self.ulimit):
            print("target violates limits")
            return -1
        else:
            self.tarPos = dest
            if self.tarPos == self.curPos:
                print("Already at target position " + str(self.tarPos))
                return 0
            else:
                print("target: " + str(self.tarPos) + " [mm]")
                if self.axistype == AXISTYPE['Rho']:
                    self.tarSteps = round(self.tarPos * SPR / (pi*DRHO))
                    print("target: " + str(self.tarSteps) + " [steps]")
                    for x in range(abs(self.tarSteps - self.curSteps)):
                        if self.curSteps < self.tarSteps:
                            GPIO.output(RH_DIR, CW)
                            GPIO.output(RH_STEP, GPIO.HIGH)
                            sleep(delay)
                            GPIO.output(RH_STEP, GPIO.LOW)
                            sleep(delay)
                            self.curSteps += 1
                        else:
                            GPIO.output(RH_DIR, CCW)
                            GPIO.output(RH_STEP, GPIO.HIGH)
                            sleep(delay)
                            GPIO.output(RH_STEP, GPIO.LOW)
                            sleep(delay)
                            self.curSteps -= 1
                        self.curPos = self.curSteps * pi * DRHO / SPR
                    self.printState()    
                return 0
        
    
try:
    setup_steppermotors()
    
    rho = axis(AXISTYPE['Rho'], -5, 100)
    rho.printState()
    rho.homing()
    
    rho.goTo(10)
    rho.printState()
    sleep(5)
    
    rho.goTo(20)
    rho.printState()
    sleep(5)
    
    rho.goTo(80)
    rho.printState()
    sleep(5)
    
    rho.goTo(0)
    rho.printState()
    sleep(5)
    print("Main loop done")
    
finally:
    # shut down cleanly
    GPIO.cleanup()
    print("Exited normally")

