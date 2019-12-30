import RPi.GPIO as GPIO
import logging
import math
from time import sleep

# Theta Axis
TH_DIR = 5               # Direction GPIO Pin
TH_STEP = 6              # Step GPIO Pin
TH_MODE = (26, 19, 13)   # Microstep Resolution GPIO Pins
TH_GEAR = 28/600         # Gear ratio of motor:theta-axis
TH_DELAY = 0.002 / 32    # Delay for movement in theta axis [s]

# Rho Axis
RH_DIR = 21              # Direction GPIO Pin
RH_STEP = 20             # Step GPIO Pin
RH_MODE = (22, 27, 17)   # Microstep Resolution GPIO Pins
RH_D = 14                # Diameter spur gear of Rho axis [mm]
RH_DELAY = 0.006 / 32    # Delay for movement in rho axis [s]

CW = 1         # Clockwise Rotation
CCW = 0        # Counterclockwise Rotation
SPR = 200*32   # Steps per Revolution

AXISTYPE = {
    'Rho': 0,
    'Theta': 1}

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
    def __init__(self, axistype, axis_min, axis_max):
        self.axistype = axistype  # from dictionary AXISTYPE
        self.axis_min = axis_min  # lower limit  [in rad or mm]
        self.axis_max = axis_max  # upper limit [in rad or mm]
        self.curSteps = 0         # current position [in steps]
        self.curPos = 0           # current position [in rad or mm]
        self.tarSteps = 0         # target position [in steps]
        self.tarPos = 0           # target position [im rad or mm]
        self.homed = False        # turns True once homed
        if self.axistype == AXISTYPE['Theta']:
            self.axisname = "Theta"
        elif self.axistype == AXISTYPE['Rho']:
            self.axisname = "Rho"        
        else:
            logging.error("Unknown axis type (should never happen)")
    
    def state(self):
        state_str = self.axisname + ": (" + str(self.curSteps) + ", " + str(self.curPos) + ", " + str(self.tarSteps) + ", " + str(self.tarPos) + ") (curSteps, curPos, tarSteps, tarPos)"
        return state_str
        
    def homing(self):
        # Drive until we see the homing switch. Not implemented yet.
        self.curSteps = self.curPos = 0
        self.homed = True
        
    def goTo(self, dest):    # destination position [in rad or mm]
        logging.debug(self.axisname + " goTo: " + str(dest))
        if not self.homed:
            logging.error(self.axisname + " not homed!")
            return -1
        elif (dest < self.axis_min) or (dest > self.axis_max):
            logging.error(self.axisname + " target violates limits")
            return -1
        else:
            self.tarPos = round(dest, 4)
            if self.tarPos == self.curPos:
                logging.info(self.axisname + " already at target position " + str(self.tarPos))
                return 0
            else:
                if self.axistype == AXISTYPE['Rho']:
                    self.tarSteps = round(self.tarPos * SPR / (math.pi*RH_D))
                    logging.debug(self.axisname + " target = " + str(self.tarPos) + "[mm]   " + str(self.tarSteps) + " [steps]")
                    for x in range(abs(self.tarSteps - self.curSteps)):
                        if self.curSteps < self.tarSteps:
                            GPIO.output(RH_DIR, CW)
                            GPIO.output(RH_STEP, GPIO.HIGH)
                            sleep(RH_DELAY)
                            GPIO.output(RH_STEP, GPIO.LOW)
                            sleep(RH_DELAY)
                            self.curSteps += 1
                        else:
                            GPIO.output(RH_DIR, CCW)
                            GPIO.output(RH_STEP, GPIO.HIGH)
                            sleep(RH_DELAY)
                            GPIO.output(RH_STEP, GPIO.LOW)
                            sleep(RH_DELAY)
                            self.curSteps -= 1
                        self.curPos = round(self.curSteps * math.pi * RH_D / SPR, 4)
                elif self.axistype == AXISTYPE['Theta']:
                    self.tarSteps = round(self.tarPos * SPR / (2*math.pi) / TH_GEAR)    # SPR is steps for 2*math.pi
                    logging.debug(self.axisname + " target = " + str(self.tarPos) + "[rad]   " + str(self.tarSteps) + " [steps]")
                    for x in range(abs(self.tarSteps - self.curSteps)):
                        if self.curSteps < self.tarSteps:
                            GPIO.output(TH_DIR, CW)
                            GPIO.output(TH_STEP, GPIO.HIGH)
                            sleep(TH_DELAY)
                            GPIO.output(TH_STEP, GPIO.LOW)
                            sleep(TH_DELAY)
                            self.curSteps += 1
                        else:
                            GPIO.output(TH_DIR, CCW)
                            GPIO.output(TH_STEP, GPIO.HIGH)
                            sleep(TH_DELAY)
                            GPIO.output(TH_STEP, GPIO.LOW)
                            sleep(TH_DELAY)
                            self.curSteps -= 1
                        self.curPos = round(self.curSteps * 2 * math.pi / SPR * TH_GEAR, 4)
                else:
                    logging.error("Unknown axis type (should never happen)")
                    return -1
                logging.debug(self.state())
                return 0

    def stripTheta(self):   # strip the theta axis of its rotations
        if self.axistype == AXISTYPE['Theta']:
            logging.info("Before stripping 2*pi: " + self.state())
            self.curPos = self.curPos % (2*math.pi)
            self.curSteps = round(self.curPos * SPR / (2*math.pi) / TH_GEAR)    # SPR is steps for 2*math.pi
            logging.info("After stripping 2*pi: " + self.state())