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

# Rho Axis
RH_DIR = 21              # Direction GPIO Pin
RH_STEP = 20             # Step GPIO Pin
RH_MODE = (22, 27, 17)   # Microstep Resolution GPIO Pins
RH_D = 14                # Diameter spur gear of Rho axis [mm]
RH_MAX = 180             # Maximum value for Rho axis
RH_MIN = -5              # Minimum value for Rho axis

STEP_DELAY = 0.002 / 32  # [s] delay between stepper motor steps (~ 1/"speed")


CW = 1         # Clockwise Rotation
CCW = 0        # Counterclockwise Rotation
SPR = 200*32   # Steps per Revolution

sign = lambda x: (1, -1)[x < 0]

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
        self.curPos = [0.0, 0.0]       # [rad mm]      current position
        self.curSteps = [0, 0]         # [steps steps] current position
        self.tarPos = [0.0, 0.0]       # [rad mm]      target position
        self.tarSteps = [0, 0]         # [steps steps] target position
        self.tarRemainder = [0.0, 0.0] # [rad mm]      remainder after rounding target to nearest steps
        self.homed = False             # turns True once homed
        
    def curState(self):
        state_str = str(self.curPos) + " [rad mm] " + str(self.curSteps) + " [steps steps]"
        return state_str
        
    def homing(self):
        # TODO: Drive until we see the homing switch. Not implemented yet.
        self.homed = True
        
    def goTo(self, dest):    # destination position [in rad and mm]
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
            self.tarPos[0] = round(dest[0], 5)
            self.tarPos[1] = round(dest[1], 5)
            if (self.tarPos[0] == self.curPos[0]) and (self.tarPos[1] == self.curPos[1]):
                logging.info("Already at target position " + str(self.tarPos))
                return 0
            else:
                # SPR is steps for 2*math.pi
                # Get int part of division for number of steps, save remainder as the rad that cannot be moved yet
                quotient, remainder = divmod(self.tarPos[0] * SPR / (2*math.pi) / TH_GEAR, 1)
                self.tarSteps[0] = int(quotient)
                self.tarRemainder[0] = remainder
                quotient, remainder = divmod(SPR / (math.pi * RH_D) * self.tarPos[1] - self.tarSteps[0] * TH_GEAR, 1)
                self.tarSteps[1] = int(quotient)
                self.tarRemainder[1] = remainder
                
                logging.debug("goTo: " + str(self.tarPos) + " [rad mm] " + str(self.tarSteps) + " [steps steps]")
                #logging.debug("remainder: " + str(self.tarRemainder) + " [rad mm]")


                deltaSteps = [(self.tarSteps[0] - self.curSteps[0]), (self.tarSteps[1] - self.curSteps[1])]
                logging.debug("delta: " + str(deltaSteps) + " [steps steps] (loop 1)")

                if deltaSteps[0] > 0:   # Differentiate rotation direction based on deltaSteps
                    GPIO.output(TH_DIR, CW)
                else:
                    GPIO.output(TH_DIR, CCW)
                if deltaSteps[1] > 0:   # Differentiate rotation direction based on deltaSteps
                    GPIO.output(RH_DIR, CW)
                else:
                    GPIO.output(RH_DIR, CCW)
                sleep(STEP_DELAY)         # Give output time to set. Unsure if necessary

                if abs(deltaSteps[0]) >= abs(deltaSteps[1]):    # More steps in THETA than there are in RHO
                    # Calculate how after how many THETA iterations the RHO axis is to be moved
                    if deltaSteps[1] != 0:
                        factorial = math.floor(deltaSteps[0] / deltaSteps[1])
                    else:
                        factorial = math.inf
                        
                    for x in range(abs(deltaSteps[0])):
                        GPIO.output(TH_STEP, GPIO.HIGH)
                        if (x % factorial == 0):
                            GPIO.output(RH_STEP, GPIO.HIGH)
                        sleep(STEP_DELAY)
                        GPIO.output(TH_STEP, GPIO.LOW)
                        if (x % factorial == 0):
                            GPIO.output(RH_STEP, GPIO.LOW)
                        sleep(STEP_DELAY)
                        self.curSteps[0] = self.curSteps[0] + int(sign(deltaSteps[0])) # inrecement or decrement based on direction
                        if (x % factorial == 0):
                            self.curSteps[1] = self.curSteps[1] + int(sign(deltaSteps[1])) # inrecement or decrement based on direction
                        self.curPos[0] = round(self.curSteps[0] * 2 * math.pi / SPR * TH_GEAR, 4)
                        self.curPos[1] = round(math.pi * RH_D / SPR * (self.curSteps[1] + self.curSteps[0] * TH_GEAR), 4)
                else:  # More steps in RHO than there are in THETA
                        # Calculate how after how many RHO iterations the THETA axis is to be moved
                    if deltaSteps[0] != 0:
                        factorial = math.floor(deltaSteps[1] / deltaSteps[0])
                    else:
                        factorial = math.inf
                        
                    for x in range(abs(deltaSteps[1])):
                        GPIO.output(RH_STEP, GPIO.HIGH)
                        if (x % factorial == 0):
                            GPIO.output(TH_STEP, GPIO.HIGH)
                        sleep(STEP_DELAY)
                        GPIO.output(RH_STEP, GPIO.LOW)
                        if (x % factorial == 0):
                            GPIO.output(TH_STEP, GPIO.LOW)
                        sleep(STEP_DELAY)
                        self.curSteps[1] = self.curSteps[1] + int(sign(deltaSteps[1])) # inrecement or decrement based on direction
                        if (x % factorial == 0):
                            self.curSteps[0] = self.curSteps[0] + int(sign(deltaSteps[0])) # inrecement or decrement based on direction
                        self.curPos[0] = round(self.curSteps[0] * 2 * math.pi / SPR * TH_GEAR, 4)
                        self.curPos[1] = round(math.pi * RH_D / SPR * (self.curSteps[1] + self.curSteps[0] * TH_GEAR), 4)
                
                logging.debug("Position after double axis move: " + self.curState())
                
                # Due to the unequal number of steps, one of the two axes will not yet be at the target destination. Move single axis to correct this.
                deltaSteps = [(self.tarSteps[0] - self.curSteps[0]), (self.tarSteps[1] - self.curSteps[1])]
                logging.debug("delta: " + str(deltaSteps) + " [steps steps] (loop 2)")
                if deltaSteps[0] != 0:
                    for x in range(abs(deltaSteps[0])):
                            GPIO.output(TH_STEP, GPIO.HIGH)
                            sleep(STEP_DELAY)
                            GPIO.output(TH_STEP, GPIO.LOW)
                            sleep(STEP_DELAY)
                            self.curSteps[0] = self.curSteps[0] + int(sign(deltaSteps[0])) # inrecement or decrement based on direction
                            self.curPos[0] = round(self.curSteps[0] * 2 * math.pi / SPR * TH_GEAR, 4)
                            self.curPos[1] = round(math.pi * RH_D / SPR * (self.curSteps[1] + self.curSteps[0] * TH_GEAR), 4)
                if deltaSteps[1] != 0:
                    for x in range(abs(deltaSteps[1])):
                            GPIO.output(RH_STEP, GPIO.HIGH)
                            sleep(STEP_DELAY)
                            GPIO.output(RH_STEP, GPIO.LOW)
                            sleep(STEP_DELAY)
                            self.curSteps[1] = self.curSteps[1] + int(sign(deltaSteps[1])) # inrecement or decrement based on direction
                            self.curPos[0] = round(self.curSteps[0] * 2 * math.pi / SPR * TH_GEAR, 4)
                            self.curPos[1] = round(math.pi * RH_D / SPR * (self.curSteps[1] + self.curSteps[0] * TH_GEAR), 4)
                
                logging.debug("Position after single axis move: " + self.curState())
                return 0

    def stripTheta(self):   # strip the theta axis of its rotations
        logging.debug("Pos before stripping 2*pi: " + self.curState())
        # Round to the nearest circle (+2pi or -2pi)
        div, remain = divmod(self.curPos[0], sign(self.curPos[0])*2*math.pi)
        logging.debug("Circles: " + str(div) + " remainder: " + str(remain))
        self.curPos[0] = remain
        self.curSteps[0] = round(self.curPos[0] * SPR / (2*math.pi) / TH_GEAR)    # SPR is steps for 2*math.pi
        #Subtract or add the number of steps that RHO would have corrected in the div number of circles
        self.curSteps[1] += sign(self.curPos[0])*int(div*SPR)
        logging.debug("Pos after stripping 2*pi: " + self.curState())
        return 0