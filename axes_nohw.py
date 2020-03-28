import logging
import math
import time
from numpy import sign

SPR = 200*32             # Steps per revolution (NEMA = 200 steps/rev, microstepping 1/32)

# Axes Configuration: [Theta Axis, Rho Axis]
DIR = [5, 21]            # GPIO pin: Stepper motor set direction
STEP = [6, 20]           # GPIO pin: Stepper motor trigger step
MODE = [(26, 19, 13), (22, 27, 17)]   # GPIO pin: Stepper motor microstep resolution
GEAR = [28/600, 14]      # [Gear ratio of motor:THETA-axis, diameter spur gear RHO axis [mm]]
TOL = [2*math.pi*GEAR[0]/SPR, math.pi*GEAR[1]/SPR]  # [rad, mm] tolerance when comparing two positions (1 step error)
HOME = [18, 23, 0]       # GPIO pin number for homing switches [THETA 1, THETA 2, RHO]

# Rho Axis
RH_MAX = 150             # Maximum value for RHO axis in [mm]
RH_MIN = -2              # Minimum value for RHO axis in [mm]

# Other constants
STEP_DELAY = 0.01      # [s] delay between stepper motor steps (~ 1/"speed")
PRECISION = 5            # Number of decimal places
ROTATION = 2*math.pi     # [rad] to improve readability

# Run states "dictionary"
INIT = 0
HOMING_A = 1
HOMING_B = 2
HOMING_C = 3
HOMED = 4

sign = lambda x: (1, -1)[x < 0]

def setup_steppermotors():
    RESOLUTION = {'Full': (0, 0, 0),
                  'Half': (1, 0, 0),
                  '1/4': (0, 1, 0),
                  '1/8': (1, 1, 0),
                  '1/16': (0, 0, 1),
                  '1/32': (1, 0, 1)}

def cleanup():
    pass

def sleep(millis):
    pass
    
class thetarho:
    def __init__(self):
        self.curPos = [0.0, 0.0]       # [rad mm]      current position
        self.curSteps = [0, 0]         # [steps steps] current position
        self.tarPos = [0.0, 0.0]       # [rad mm]      target position
        self.tarSteps = [0, 0]         # [steps steps] target position
        self.homingSteps = [0, 0]      # [steps steps] homing switch position (temporary reference value)
        self.runState = INIT           # Set to "HOMED" once homing is completed
        
    # Return current state (= position and steps)
    def curState(self):
        state_str = str(self.curPos) + " [rad mm] " + str(self.curSteps) + " [steps steps]"
        return state_str
        
    # For a given magnet position in [rad, mm], calculate the corresponding motor position in [steps, steps]
    def convertPosToSteps(self, argPos): # argPos in [rad mm]
        # SPR is steps for 2*math.pi
        res0 = round(argPos[0] * SPR / (2*math.pi) / GEAR[0])
        res1 = round((argPos[1] / GEAR[1] - argPos[0] / 2 ) * SPR / math.pi)
        #res11 = round(argPos[1] * SPR / math.pi / GEAR[1] - res0 * GEAR[0])
        #logging.debug("Comparing calculations: Using steps: " + str(res11) + " using rad: " + str(res1))
        return [res0, res1]
    
    # For a given motor position in [steps, steps], calculate the corresponding magnet position in [rad, mm]
    def convertStepsToPos(self, argSteps): # argSteps in [steps, steps]
        res0 = round(argSteps[0] / SPR * (2*math.pi) * GEAR[0], PRECISION)
        res1 = round(GEAR[1] * ( argSteps[1] * math.pi / SPR + res0 / 2), PRECISION)
        #res11 = round(math.pi * GEAR[1] / SPR * (argSteps[1] - argSteps[0] * GEAR[0]), PRECISION)
        #logging.debug("Comparing calculations: Using steps: " + str(res11) + " using rad: " + str(res1))
        return [res0, res1]    
        
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
    
    # Move axes to reach dest position
    def goTo(self, dest):    # destination position [in rad and mm]
        if (dest[1] < RH_MIN) or (dest[1] > RH_MAX):
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

            sleep(STEP_DELAY)         # Give output time to set. Unsure if necessary
            moveBothAxes = False      # Variable used later to prevent checking (x % factorial == 0) every time 
            
            if abs(deltaSteps[0]) >= abs(deltaSteps[1]):    # More steps in THETA than there are in RHO
                # After how many steps of THETA we step in RHO
                if deltaSteps[1] != 0:
                    if (deltaSteps[0] / deltaSteps[1] >= 0): # eg. round 21.42 up to 22
                        factorial = math.ceil(deltaSteps[0] / deltaSteps[1])
                    else:                                    # eg. round -2.56 down to -3
                        factorial = math.floor(deltaSteps[0] / deltaSteps[1])
                else:
                    factorial = math.inf
                logging.debug(str(factorial) + " times more THETA steps than RHO steps.")
                
                for x in range(abs(deltaSteps[0])):
                    if ((x+1) % factorial == 0):
                        moveBothAxes = True
                    else:
                        moveBothAxes = False
                    
                    sleep(STEP_DELAY)
                    sleep(STEP_DELAY)
                    self.curSteps[0] += int(sign(deltaSteps[0])) # inrecement or decrement based on direction
                    if moveBothAxes:
                        self.curSteps[1] += int(sign(deltaSteps[1])) # inrecement or decrement based on direction
            
                self.curPos = self.convertStepsToPos(self.curSteps)
                    
            else:  # More steps in RHO than there are in THETA
                   # After how many steps of RHO we step in THETA
                if deltaSteps[0] != 0:
                    if (deltaSteps[1] / deltaSteps[0] >= 0): # eg. round 21.42 up to 22
                        factorial = math.ceil(deltaSteps[1] / deltaSteps[0])
                    else:                                    # eg. round -2.56 down to -3
                        factorial = math.floor(deltaSteps[1] / deltaSteps[0])
                else:
                    factorial = math.inf
                logging.debug(str(factorial) + " times more RHO steps than THETA steps.")
                
                for x in range(abs(deltaSteps[1])):
                    if ((x+1) % factorial == 0):
                        moveBothAxes = True
                    else:
                        moveBothAxes = False
                    sleep(STEP_DELAY)
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
                sleep(STEP_DELAY)         # Give output time to set. Unsure if necessary
                for x in range(abs(deltaSteps[0])):
                    sleep(STEP_DELAY)
                    sleep(STEP_DELAY)
                    self.curSteps[0] += int(sign(deltaSteps[0])) # inrecement or decrement based on direction
            if deltaSteps[1] != 0:
                sleep(STEP_DELAY)         # Give output time to set. Unsure if necessary
                for x in range(abs(deltaSteps[1])):
                    sleep(STEP_DELAY)
                    sleep(STEP_DELAY)
                    self.curSteps[1] += int(sign(deltaSteps[1])) # inrecement or decrement based on direction
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
        logging.debug("Circles: " + str(div) + " remainder: " + str(round(remain, PRECISION)))
        self.curPos[0] = remain
        
        self.curSteps[0] = round(self.curPos[0] * SPR / (2*math.pi) / GEAR[0])    # SPR is steps for 2*math.pi
        #Subtract or add the number of steps that RHO would have corrected in the div number of circles
        self.curSteps[1] += sign(self.curPos[0])*int(div*SPR)
        logging.debug("Pos after stripping 2*pi: " + self.curState())
        
        return 0
    
    # Find zero positions of stepper motors using hall switches
    def homing(self):
        self.runState = HOMED
