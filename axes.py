import RPi.GPIO as GPIO
import logging
import math
from time import sleep
from numpy import sign

CW = 1                   # Clockwise Rotation
CCW = 0                  # Counterclockwise Rotation
SPR = 200*32             # Steps per Revolution (NEMA = 200 Steps/rev, microstepping 1/32)

# Theta Axis
DIR = [5, 21]            # Direction GPIO Pin
STEP = [6, 20]              # Step GPIO Pin
MODE = [(26, 19, 13), (22, 27, 17)]   # Microstep Resolution GPIO Pins
GEAR = [28/600, 14*0.995]      # [Gear ratio of motor:THETA-axis, diameter spur gear RHO axis [mm]]
TOL = [2*math.pi*GEAR[0]/SPR, math.pi*GEAR[1]/SPR]  # [rad, mm] tolerance when comparing two positions (1 step error)

# Rho Axis
RH_MAX = 170             # Maximum value for Rho axis
RH_MIN = -5              # Minimum value for Rho axis

STEP_DELAY = 0.0001      # [s] delay between stepper motor steps (~ 1/"speed")
PRECISION = 5            # Number of decimal places


sign = lambda x: (1, -1)[x < 0]

def setup_steppermotors():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DIR[0], GPIO.OUT)
    GPIO.setup(DIR[1], GPIO.OUT)
    GPIO.setup(STEP[0], GPIO.OUT)
    GPIO.setup(STEP[1], GPIO.OUT)
    GPIO.output(DIR[0], CW)
    GPIO.output(DIR[0], CW)

    GPIO.setup(MODE[0], GPIO.OUT)
    GPIO.setup(MODE[1], GPIO.OUT)
    RESOLUTION = {'Full': (0, 0, 0),
                  'Half': (1, 0, 0),
                  '1/4': (0, 1, 0),
                  '1/8': (1, 1, 0),
                  '1/16': (0, 0, 1),
                  '1/32': (1, 0, 1)}
    GPIO.output(MODE[0], RESOLUTION['1/32'])
    GPIO.output(MODE[0], RESOLUTION['1/32'])

    
class thetarho:
    def __init__(self):
        self.curPos = [0.0, 0.0]       # [rad mm]      current position
        self.curSteps = [0, 0]         # [steps steps] current position
        self.tarPos = [0.0, 0.0]       # [rad mm]      target position
        self.tarSteps = [0, 0]         # [steps steps] target position
        self.homed = False             # turns True once homed
        
    # Return current state (= position and steps)
    def curState(self):
        state_str = str(self.curPos) + " [rad mm] " + str(self.curSteps) + " [steps steps]"
        return state_str
        
    # TODO: Drive until we see the homing switch. Not implemented yet.
    def homing(self):
        self.homed = True

    # Check if current position is within a tolerance window of the position passsed as an argument
    def withinTolerance(self, dest): 
        if (self.curPos[0] >= dest[0] - TOL[0]) and \
           (self.curPos[0] <= dest[0] + TOL[0]) and \
           (self.curPos[1] >= dest[1] - TOL[1]) and \
           (self.curPos[1] <= dest[1] + TOL[1]):
            #logging.debug("Currently within tolerance window of " + str(dest))
            return True
        else:
            #logging.debug("Currently outside tolerance window of " + str(dest))
            return False
    
    # For a given position in [rad, mm], calculate the corresponding motor steps in [steps, steps]
    def convertPosToSteps(self, argPos): # argPos in [rad mm]
        # SPR is steps for 2*math.pi
        res0 = round(argPos[0] * SPR / (2*math.pi) / GEAR[0])
        res1 = round(SPR / (math.pi * GEAR[1]) * argPos[1] - res0 * GEAR[0])
        return [res0, res1]
    
    # For a given steps in [steps, steps], calculate the corresponding position in [rad, mm]
    def convertStepsToPos(self, argSteps): # argSteps in [steps, steps]
        res0 = round(argSteps[0] * 2 * math.pi / SPR * GEAR[0], PRECISION)
        res1 = round(math.pi * GEAR[1] / SPR * (argSteps[1] + argSteps[0] * GEAR[0]), PRECISION)
        return [res0, res1]
    
    # Move axes to reach dest position
    def goTo(self, dest):    # destination position [in rad and mm]
        if not self.homed:
            logging.error("Not homed!")
            return -1
        elif (dest[1] < RH_MIN) or (dest[1] > RH_MAX):
            logging.error("Target violates RHO axis limits")
            return -1
        elif (self.withinTolerance(dest)):
                logging.info("Already at target position " + str(self.tarPos))
                return 0
        else:
            self.tarPos[0] = round(dest[0], PRECISION)
            self.tarPos[1] = round(dest[1], PRECISION)
            self.tarSteps = self.convertPosToSteps(self.tarPos)
            
            logging.debug("goTo: " + str(self.tarPos) + " [rad mm] " + str(self.tarSteps) + " [steps steps]")
            
            deltaSteps = [(self.tarSteps[0] - self.curSteps[0]), (self.tarSteps[1] - self.curSteps[1])]
            logging.debug("delta: " + str(deltaSteps) + " [steps steps] (loop 1)")

            if deltaSteps[0] > 0:   # Differentiate rotation direction based on deltaSteps
                GPIO.output(DIR[0], CW)
            else:
                GPIO.output(DIR[0], CCW)
            if deltaSteps[1] > 0:   # Differentiate rotation direction based on deltaSteps
                GPIO.output(DIR[1], CW)
            else:
                GPIO.output(DIR[1], CCW)
            sleep(STEP_DELAY)         # Give output time to set. Unsure if necessary
            moveBothAxes = False      # Variable used later to prevent checking (x % factorial == 0) every time 
            
            if abs(deltaSteps[0]) >= abs(deltaSteps[1]):    # More steps in THETA than there are in RHO
                # te how after how many THETA iterations the RHO axis is to be moved
                if deltaSteps[1] != 0:
                    if deltaSteps[1] > 0: # if moving in positive RHO, round down to next integer factor to undershoot
                        factorial = math.floor(deltaSteps[0] / deltaSteps[1])
                    else: # if moving in negative RHO, round up to next integer to undershoot
                        factorial = math.floor(deltaSteps[0] / deltaSteps[1])
                else:
                    factorial = math.inf
                logging.debug(str(factorial) + " times more THETA steps than RHO steps.")
                
                for x in range(abs(deltaSteps[0])):
                    GPIO.output(STEP[0], GPIO.HIGH)
                    if (x % factorial == 0):
                        GPIO.output(STEP[1], GPIO.HIGH)
                        moveBothAxes = True
                    else:
                        moveBothAxes = False
                    sleep(STEP_DELAY)
                    GPIO.output(STEP[0], GPIO.LOW)
                    if moveBothAxes:
                        GPIO.output(STEP[1], GPIO.LOW)
                    sleep(STEP_DELAY)
                    self.curSteps[0] = self.curSteps[0] + int(sign(deltaSteps[0])) # inrecement or decrement based on direction
                    if moveBothAxes:
                        self.curSteps[1] += int(sign(deltaSteps[1])) # inrecement or decrement based on direction
                self.curPos = self.convertStepsToPos(self.curSteps)
                    
            else:  # More steps in RHO than there are in THETA
                    # Calculate how after how many RHO iterations the THETA axis is to be moved
                if deltaSteps[0] != 0:
                    if deltaSteps[0] > 0:
                        factorial = math.floor(deltaSteps[1] / deltaSteps[0])
                    else:
                        factorial = math.ceil(deltaSteps[1] / deltaSteps[0])
                else:
                    factorial = math.inf
                logging.debug(str(factorial) + " times more RHO steps than THETA steps.")
                
                for x in range(abs(deltaSteps[1])):
                    GPIO.output(STEP[1], GPIO.HIGH)
                    if (x % factorial == 0):
                        GPIO.output(STEP[0], GPIO.HIGH)
                        moveBothAxes = True
                    else:
                        moveBothAxes = False
                    sleep(STEP_DELAY)
                    GPIO.output(STEP[1], GPIO.LOW)
                    if moveBothAxes:
                        GPIO.output(STEP[0], GPIO.LOW)
                    sleep(STEP_DELAY)
                    self.curSteps[1] += int(sign(deltaSteps[1])) # inrecement or decrement based on direction
                    if moveBothAxes:
                        self.curSteps[0] += int(sign(deltaSteps[0])) # inrecement or decrement based on direction
                self.curPos = self.convertStepsToPos(self.curSteps)
            
            logging.debug("Position after double axis move: " + self.curState())
            
            # Due to the unequal number of steps, one of the two axes will not yet be at the target destination. Move single axis to correct this.
            deltaSteps = [(self.tarSteps[0] - self.curSteps[0]), (self.tarSteps[1] - self.curSteps[1])]
            logging.debug("delta: " + str(deltaSteps) + " [steps steps] (loop 2)")
            if deltaSteps[0] != 0:
                for x in range(abs(deltaSteps[0])):
                    GPIO.output(STEP[0], GPIO.HIGH)
                    sleep(STEP_DELAY)
                    GPIO.output(STEP[0], GPIO.LOW)
                    sleep(STEP_DELAY)
                    self.curSteps[0] += int(sign(deltaSteps[0])) # inrecement or decrement based on direction
                self.curPos = self.convertStepsToPos(self.curSteps)
            if deltaSteps[1] != 0:
                for x in range(abs(deltaSteps[1])):
                    GPIO.output(STEP[1], GPIO.HIGH)
                    sleep(STEP_DELAY)
                    GPIO.output(STEP[1], GPIO.LOW)
                    sleep(STEP_DELAY)
                    self.curSteps[1] +=int(sign(deltaSteps[1])) # inrecement or decrement based on direction
                self.curPos = self.convertStepsToPos(self.curSteps)
            
            logging.debug("Position after single axis move: " + self.curState())
            return 0

    # Strip the position of the axes to within a +/- 2Pi circle. Affects both THETA and RHO 
    def stripTheta(self):
        # After an exception, curPos might not be up to date with the curSteps
        self.curPos = self.convertStepsToPos(self.curSteps)
        
        logging.debug("Pos before stripping 2*pi: " + self.curState())
        # Round to the nearest circle (+2pi or -2pi)
        div, remain = divmod(self.curPos[0], sign(self.curPos[0])*2*math.pi)
        logging.debug("Circles: " + str(div) + " remainder: " + str(remain))
        self.curPos[0] = remain
        self.curSteps[0] = round(self.curPos[0] * SPR / (2*math.pi) / GEAR[0])    # SPR is steps for 2*math.pi
        #Subtract or add the number of steps that RHO would have corrected in the div number of circles
        self.curSteps[1] += sign(self.curPos[0])*int(div*SPR)
        logging.debug("Pos after stripping 2*pi: " + self.curState())
        return 0