import RPi.GPIO as GPIO
import logging
import math
from time import sleep
from numpy import sign

CW = GPIO.LOW            # Clockwise rotation
CCW = GPIO.HIGH          # Counterclockwise rotation
SPR = 200*32             # Steps per revolution (NEMA = 200 steps/rev, microstepping 1/32)

# Axes Configuration: [Theta Axis, Rho Axis]
DIR = [5, 21]            # GPIO pin: Stepper motor set direction
STEP = [6, 20]           # GPIO pin: Stepper motor trigger step
MODE = [(26, 19, 13), (22, 27, 17)]   # GPIO pin: Stepper motor microstep resolution
HOME = [25, 24, 23]       # GPIO pin number for homing switches [THETA 1, THETA 2, RHO]
ENABLE = [16, 12]         # GPIO pin number for enabling stepper motors [THETA, RHO]
GEAR = [28/600, 14]      # [Gear ratio of motor:THETA-axis, diameter spur gear RHO axis [mm]]
TOL = [2*math.pi*GEAR[0]/SPR, math.pi*GEAR[1]/SPR]  # [rad, mm] tolerance when comparing two positions (1 step error)

# Rho Axis
RH_MAX = 176             # Maximum value for RHO axis in [mm]
RH_MIN = -2              # Minimum value for RHO axis in [mm]
RH_HOME_SENSOR_POS = 176 # RHO axis position when home switch of RHO is activated [mm]
                         # This is a parameter that has to be tuned depending on physical mounting and sensor sensitivity.
                         # To tune: Mark desired axis 0 position on rho axis and linear guide.
                         # Extend RHO until the sensor triggers. Measure distance from 0 to this mark im mm. Adjust here.

# Other constants
STEP_DELAY = 0.0001      # [s] delay between stepper motor steps (~ 1/"speed")
PRECISION = 5            # Number of decimal places
ROTATION = 2*math.pi     # [rad] to improve readability

# Run states "dictionary"
runState = {
    'INIT'     : 0,
    'HOMING_A' : 1,
    'HOMING_B' : 2,
    'HOMING_C' : 3,
    'HOMING_D' : 4,
    'HOMING_E' : 5,
    'HOMING_F' : 6,
    'HOMED'    : 7,
    }


sign = lambda x: (1, -1)[x < 0]

def setup_steppermotors():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DIR[0], GPIO.OUT)
    GPIO.setup(DIR[1], GPIO.OUT)
    GPIO.output(DIR[0], CW)
    GPIO.output(DIR[1], CW)

    GPIO.setup(STEP[0], GPIO.OUT)
    GPIO.setup(STEP[1], GPIO.OUT)
    GPIO.setup(HOME[0], GPIO.IN)
    GPIO.setup(HOME[1], GPIO.IN)
    GPIO.setup(HOME[2], GPIO.IN)

    GPIO.setup(MODE[0], GPIO.OUT)
    GPIO.setup(MODE[1], GPIO.OUT)
    RESOLUTION = {'Full': (0, 0, 0),
                  'Half': (1, 0, 0),
                  '1/4': (0, 1, 0),
                  '1/8': (1, 1, 0),
                  '1/16': (0, 0, 1),
                  '1/32': (1, 0, 1)}
    GPIO.output(MODE[0], RESOLUTION['1/32'])
    GPIO.output(MODE[1], RESOLUTION['1/32'])

    #Enable / disable pins
    GPIO.setup(ENABLE[0], GPIO.OUT)
    GPIO.setup(ENABLE[1], GPIO.OUT)
    steppers_disable()

def homing_switch_states():
    logging.debug("Homing sensors: " + str(GPIO.input(HOME[0])) + ", " + str(GPIO.input(HOME[1])) + ", " + str(GPIO.input(HOME[2])))


def steppers_enable():
    GPIO.output(ENABLE[0], True)
    GPIO.output(ENABLE[1], True)
    sleep(0.003) #DRV8825 takes 1.7ms to wake up
    logging.debug("Enabled stepper motors (output enable = True)")

def steppers_disable():
    GPIO.output(ENABLE[0], False)
    GPIO.output(ENABLE[1], False)
    sleep(0.003) #DRV8825 takes 1.7ms to wake up. Assuming similar to go to sleep.
    logging.debug("Disabled stepper motors (output enable = False)")

def cleanup():
    GPIO.cleanup()
    logging.debug("GPIO.cleanup() performed")
    
class thetarho:
    def __init__(self):
        self.curPos = [0.0, 0.0]       # [rad mm]      current position
        self.curSteps = [0, 0]         # [steps steps] current position
        self.tarPos = [0.0, 0.0]       # [rad mm]      target position
        self.tarSteps = [0, 0]         # [steps steps] target position
        self.runState = runState['INIT'] # Set to "HOMED" once homing is completed

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
        #TODO: Fix this alternate calculation... something is off (don't match up).
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
        if (dest[1] < RH_MIN and (self.runState != runState['HOMING_E'])) or \
                (dest[1] > RH_MAX and (self.runState != runState['HOMING_F'])):
            logging.error("Target violates RHO axis limits (goTo " + str(dest) + ")")
            return -1
        elif (self.withinTolerance(dest)):
                logging.info("Already at target position " + str(self.tarPos))
                return 0
        else:
            #Enable stepper motors if they are not already
            if (not GPIO.input(ENABLE[0])) or (not GPIO.input(ENABLE[1])):
                logging.warn("Steppers not yet enabled, enabling...")
                steppers_enable()

            # Set target position and convert to steps
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
                    GPIO.output(STEP[0], GPIO.HIGH)
                    if ((x+1) % factorial == 0):
                        GPIO.output(STEP[1], GPIO.HIGH)
                        moveBothAxes = True
                    else:
                        moveBothAxes = False
                    sleep(STEP_DELAY)
                    GPIO.output(STEP[0], GPIO.LOW)
                    if moveBothAxes:
                        GPIO.output(STEP[1], GPIO.LOW)
                    sleep(STEP_DELAY)
                    self.curSteps[0] += int(sign(deltaSteps[0])) # inrecement or decrement based on direction
                    if moveBothAxes:
                        self.curSteps[1] += int(sign(deltaSteps[1])) # inrecement or decrement based on direction
                    self.curPos = self.convertStepsToPos(self.curSteps)

                    #If we are in run mode HOMING_A, check if homing sensors [0] and [1] are active
                    if self.runState == runState['HOMING_A']:
                        if (not GPIO.input(HOME[0]) and (not GPIO.input(HOME[1]))):
                            homing_switch_states()
                            logging.debug("HOMING_A: Found both homing switches active at " + self.curState())
                            return 0
                    #If we are in run mode HOMING_B, check if homing sensor [0] AND [1] are inactive
                    if self.runState == runState['HOMING_B']:
                        if GPIO.input(HOME[0]) and GPIO.input(HOME[1]):
                            homing_switch_states()
                            logging.debug("HOMING_B: Found both homing switches dropped off at " + self.curState())
                            return 0
                    #If we are in run mode HOMING_C, check if homing sensor [0] AND [1] are active
                    if self.runState == runState['HOMING_C']:
                        if (not GPIO.input(HOME[0])) and (not GPIO.input(HOME[1])):
                            homing_switch_states()
                            logging.debug("HOMING_C: Found both homing switches active at " + self.curState())
                            return 0

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
                    GPIO.output(STEP[1], GPIO.HIGH)
                    if ((x+1) % factorial == 0):
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

                    #If we are in run mode HOMING_D, check if homing sensor [2] is inactive
                    if self.runState == runState['HOMING_E']:
                        if GPIO.input(HOME[2]):
                            logging.debug("HOMING_E: Home switch RHO dropped off at " + self.curState())
                            return 0

                    #If we are in run mode HOMING_F, check if homing sensor [2] is active
                    if self.runState == runState['HOMING_F']:
                        if not GPIO.input(HOME[2]):
                            logging.debug("HOMING_F: Home switch RHO triggered at " + self.curState())
                            return 0

            logging.debug("Position after double axis move: " + self.curState())

            # Due to the unequal number of steps, one of the two axes will not yet be at the target destination. Move single axis to correct this.
            deltaSteps = [(self.tarSteps[0] - self.curSteps[0]), (self.tarSteps[1] - self.curSteps[1])]
            logging.debug("delta: " + str(deltaSteps) + " [steps steps] (loop 2)")

            if deltaSteps[0] != 0:
                if deltaSteps[0] > 0:   # Differentiate rotation direction based on deltaSteps
                    GPIO.output(DIR[0], CW)
                else:
                    GPIO.output(DIR[0], CCW)
                sleep(STEP_DELAY)         # Give output time to set. Unsure if necessary
                for x in range(abs(deltaSteps[0])):
                    GPIO.output(STEP[0], GPIO.HIGH)
                    sleep(STEP_DELAY)
                    GPIO.output(STEP[0], GPIO.LOW)
                    sleep(STEP_DELAY)
                    self.curSteps[0] += int(sign(deltaSteps[0])) # inrecement or decrement based on direction
            if deltaSteps[1] != 0:
                if deltaSteps[1] > 0:   # Differentiate rotation direction based on deltaSteps
                    GPIO.output(DIR[1], CW)
                else:
                    GPIO.output(DIR[1], CCW)
                sleep(STEP_DELAY)         # Give output time to set. Unsure if necessary
                for x in range(abs(deltaSteps[1])):
                    GPIO.output(STEP[1], GPIO.HIGH)
                    sleep(STEP_DELAY)
                    GPIO.output(STEP[1], GPIO.LOW)
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
        #Homing of THETA axis:
        #   HOMING_A: Move until both theta home sensors are triggered.
        #   HOMING_B: Continue motion until both sensors drop signal
        #   HOMING_C: Rotate backward until both sensors are triggered (not equal to HOMING_B due to hysterisis)
        #    -> Zero position is in the middle of HOMING_A and HOMING_C
        #   HOMING_D: Move to (0,0) position (rotates THETA axis to zero, RHO stays)
        #
        #Homing of RHO axis:
        #   HOMING_E: If homing sensor is active, retract RHO axis until it isn't
        #   HOMING_F: Homing sensor is not active, extend RHO axis until it is
        #             Set RHO axis distance to RH_HOME_SENSOR_POS.
        #   Set HOMED
        logging.info("Starting on HOMING run")

        ## Home THETA axis
        if self.runState != runState['INIT']:
            logging.warn("Homing: Calling homing in the correct place? Entering homing run...")

        ### INIT
        #If THETA axis is already at home location, move CCW until both sensors are inactive
        if (not GPIO.input(HOME[0])) and (not GPIO.input(HOME[1])):
            logging.debug("Homing: Already both sensors active, retracing 1/16 rotation")
            self.goTo([-1/16*ROTATION, 0])   # perform max of -1/16 rotation, exit when both sensors inactive

        if (not GPIO.input(HOME[0])) and (not GPIO.input(HOME[1])):
            raise RuntimeError("Homing: Homing switches for THETA are still active after -1/16 rotation... something is wrong. Exiting.")

        ### HOMING_A
        self.runState = runState['HOMING_A']
        logging.info("Homing: Setting runState = HOMING_A")

        self.goTo([1*ROTATION, 0])   # perform max of 1 rotation, exit when both sensors active
        if GPIO.input(HOME[0]) or GPIO.input(HOME[1]):
            raise RuntimeError("HOMING_A: After max 1 rotation, at least one homing switch for THETA is still inactive")

        #Both sensors must be active here. Set current position to (0,0)
        logging.info("Set current position to (0,0)")
        self.curSteps = [0, 0]
        self.curPos = [0, 0]
        sleep(1)

        ### HOMING_B
        self.runState = runState['HOMING_B']
        logging.info("Homing: Setting runState = HOMING_B")

        self.goTo([(1/8)*ROTATION, 0])   # perform max of 1/8 rotation
        if (not GPIO.input(HOME[0])) or (not GPIO.input(HOME[1])):
            raise RuntimeError("HOMING_B: Expected both homing switches to be inactive. At least one is active.")
        sleep(1)

        ### HOMING_C
         #Both sensors must be inactive here.
        self.runState = runState['HOMING_C']
        logging.info("Homing: Setting runState = HOMING_C")

        self.goTo([0, 0])   # rotate back. Max to where both switches were active in HOMING_A
        if GPIO.input(HOME[0]) or GPIO.input(HOME[1]):
            raise RuntimeError("HOMING_C: Expected both homing switches to be active. At least one is inactive.")

        #Both sensors must be active here. Set zero to be in the middle of the two positions.
        self.curSteps[0] = round(self.curSteps[0] / 2)
        self.curSteps[1] = 0
        self.curPos = self.convertStepsToPos(self.curSteps)
        logging.debug("Homing: Current position after THETA homing: " + self.curState())
        sleep(1)

        ### HOMING_D
        self.runState = runState['HOMING_D']
        logging.info("Homing: Setting runState = HOMING_D")
        self.goTo([0, 0])
        logging.debug("Homing: At THETA home position " + self.curState())
        sleep(1)

        ## Home RHO axis
        ### HOMING_E
        if not GPIO.input(HOME[2]):
            self.runState = runState['HOMING_E']
            logging.info("Homing: Setting runState = HOMING_E")
            self.goTo([0, -10]) #retract axis by 10mm, the home sensor should not be triggered then
            if not GPIO.input(HOME[2]):
                raise RuntimeError("HOMING_E: RHO homing sensor is active even after retracing by 10mm.")
            else:
                logging.info("Homing: Retracted RHO axis by " + str(self.curPos[1]) + "mm")

        ### HOMING_F
        # home sensor is inactive here
        self.runState = runState['HOMING_F']
        logging.info("Homing: Setting runState = HOMING_F")
        self.goTo([0, RH_HOME_SENSOR_POS+10]) #Move RHO axis outwards to look for homing switch (max to RH_HOME_SENSOR_POS +10 mm)
        if GPIO.input(HOME[2]):
            sleep(1)
            raise RuntimeError("HOMING_F: RHO homing sensor is inactive even after full extension by " + str(RH_HOME_SENSOR_POS+10) + "mm")

        self.curPos = [0, RH_HOME_SENSOR_POS]
        self.curSteps = self.convertPosToSteps(self.curPos)
        logging.info("Homing: Set current position to " + self.curState())
        sleep(1)

        ### HOMED
        self.runState = runState['HOMED']
        logging.info("Homing: Setting runState = HOMED")

        self.goTo([0,0])
        steppers_disable()
