from time import sleep
from math import pi
import RPi.GPIO as GPIO
import logging
import sys

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
    
    def printState(self):
        logging.info(self.axisname + ": (" + str(self.curSteps) + ", " + str(self.curPos) + ", " + str(self.tarSteps) + ", " + str(self.tarPos) + ") (curSteps, curPos, tarSteps, tarPos)")
        return 0
        
    def homing(self):
        # Drive until we see the homing switch. Not implemented yet.
        self.curSteps = self.curPos = 0
        self.homed = True
        
    def goTo(self, dest):    # destination position [in rad or mm]
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
                    self.tarSteps = round(self.tarPos * SPR / (pi*RH_D))
                    logging.info(self.axisname + " target = " + str(self.tarPos) + "[mm]   " + str(self.tarSteps) + " [steps]")
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
                        self.curPos = round(self.curSteps * pi * RH_D / SPR, 4)
                elif self.axistype == AXISTYPE['Theta']:
                    self.tarSteps = round(self.tarPos * SPR / (2*pi) / TH_GEAR)    # SPR is steps for 2*pi
                    logging.info(self.axisname + " target = " + str(self.tarPos) + "[rad]   " + str(self.tarSteps) + " [steps]")
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
                        self.curPos = round(self.curSteps * 2 * pi / SPR * TH_GEAR, 4)
                else:
                    logging.error("Unknown axis type (should never happen)")
                    return -1
                self.printState()    
                return 0

def main():
    logging.info("Starting sandtrails ")
    try:
        setup_steppermotors()
       
        logging.info("Steppermotor set up") 
        rho = axis(AXISTYPE['Rho'], -5, 100)
        theta = axis(AXISTYPE['Theta'], -0.1*pi, 2.1*pi)
        rho.printState()
        rho.homing()
        theta.homing()
    
        rho.goTo(40)
        rho.printState()
        theta.goTo(1/8*pi)
        theta.printState()
        sleep(2)
    
        """
        rho.goTo(80)
        rho.printState()
        theta.goTo(3/4*pi)
        theta.printState()
        sleep(2)
    
        theta.goTo(0)
        theta.printState()
        rho.goTo(10)
        rho.printState()
        """
        logging.info("Main loop done")
    
    except Exception as error:
        logging.error("Exception occured: " + str(error))
    finally:
        # shut down cleanly
        try: # drive axes to zero
            logging.info("Going back home")
            rho.goTo(0)
            rho.printState()
            theta.goTo(0)
            theta.printState()
        except:
            logging.error("Could not drive axes back to zero. Careful on next run, might hit physical limits")
        finally:
            GPIO.cleanup()
            logging.info("GPIO cleanup performed")

if __name__ == '__main__':
    #logging.basicConfig(filename='sandtrails.log', level=logging.INFO, format='%(levelname)s: %(message)s')
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    if sys.version_info[0] < 3:
        logging.critical("Must be using Python 3")
    else:
        main()
