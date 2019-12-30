import RPi.GPIO as GPIO
import logging
import math
from time import sleep
from numpy import sign

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
RH_MAX = 180             # Maximum value for Rho axis
RH_MIN = -5              # Minimum value for Rho axis


CW = 1         # Clockwise Rotation
CCW = 0        # Counterclockwise Rotation
SPR = 200*32   # Steps per Revolution

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

    
class thetarho:
    def __init__(self):
        self.curPos = [0.0, 0.0]  # current position [in rad and mm]
        self.curSteps = [0, 0]    # current position [in steps]
        self.tarPos = [0.0, 0.0]  # target position [in rad and mm]
        self.tarSteps = [0, 0]    # target position [in steps]
        self.homed = False        # turns True once homed
        
    def curState(self):
        state_str = str(self.curPos) + " " + str(self.curSteps) + " [curPos] [curSteps]"
        return state_str
        
    def homing(self):
        # TODO: Drive until we see the homing switch. Not implemented yet.
        self.homed = True
        
    def goTo(self, dest):    # destination position [in rad and mm]
        logging.debug("goTo: " + str(dest))
        if type(dest) != list:
            logging.error("Invalid argument (destination should be a list)")
            return -1
        elif len(dest) != 2:
            logging.error("Invalid argument (destination needs exactly two arguments)")
            return -1
        elif not self.homed:
            logging.error("Not homed!")
            return -1
        elif (dest[1] < RH_MIN) or (dest[1] > RH_MAX):
            logging.error("Target violates RHO axis limits")
            return -1
        else:
            self.tarPos[0] = round(dest[0], 4)
            self.tarPos[1] = round(dest[1], 4)
            if (self.tarPos[0] == self.curPos[0]) and (self.tarPos[1] == self.curPos[1]):
                logging.info("Already at target position " + str(self.tarPos))
                return 0
            else:
                self.tarSteps[0] = round(self.tarPos[0] * SPR / (2*math.pi) / TH_GEAR)    # SPR is steps for 2*math.pi
                logging.debug("Theta target = " + str(self.tarPos[0]) + "[rad] " + str(self.tarSteps[0]) + "[steps]")
                self.tarSteps[1] = round(SPR / (math.pi * RH_D) * self.tarPos[1] - self.tarSteps[0] * TH_GEAR)
                logging.debug("Rho target = " + str(self.tarPos[1]) + "[mm] " + str(self.tarSteps[1]) + "[steps]")

                deltaSteps = [(self.tarSteps[0] - self.curSteps[0]), (self.tarSteps[1] - self.curSteps[1])]
                
                if abs(deltaSteps[0]) < abs(deltaSteps[1]):
                    logging.error("Unhandled case where steps in theta are less than those in rho. Exiting")
                    return -1
                
                # Calculate how after how many theta iterations the rho axis is to be moved
                factorial = math.floor(deltaSteps[0] / deltaSteps[1])
                
                if deltaSteps[0] > 0:   # Differentiate rotation direction based on deltaSteps
                    GPIO.output(TH_DIR, CW)
                else:
                    GPIO.output(TH_DIR, CCW)
                if deltaSteps[1] > 0:   # Differentiate rotation direction based on deltaSteps
                    GPIO.output(RH_DIR, CW)
                else:
                    GPIO.output(RH_DIR, CCW)
                sleep(TH_DELAY)         # Give output time to set. Unsure if necessary
                    
                for x in range(abs(deltaSteps[0])):
                    GPIO.output(TH_STEP, GPIO.HIGH)
                    if (x % factorial == 0):
                        GPIO.output(RH_STEP, GPIO.HIGH)
                    sleep(TH_DELAY)
                    GPIO.output(TH_STEP, GPIO.LOW)
                    if (x % factorial == 0):
                        GPIO.output(RH_STEP, GPIO.LOW)
                    sleep(TH_DELAY)
                    self.curSteps[0] = self.curSteps[0] + int(sign(deltaSteps[0])) # inrecement or decrement based on direction
                    if (x % factorial == 0):
                        self.curSteps[1] = self.curSteps[1] + int(sign(deltaSteps[1])) # inrecement or decrement based on direction
                    self.curPos[0] = round(self.curSteps[0] * 2 * math.pi / SPR * TH_GEAR, 4)
                    self.curPos[1] = round(math.pi * RH_D / SPR * (self.curSteps[1] + self.curSteps[0] * TH_GEAR), 4)
                    
                """
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
                """
                logging.debug(self.curState())
                return 0

    def stripTheta(self):   # strip the theta axis of its rotations
        self.curPos[0] = self.curPos[0] % (2*math.pi)
        self.curSteps[0] = round(self.curPos[0] * SPR / (2*math.pi) / TH_GEAR)    # SPR is steps for 2*math.pi
        