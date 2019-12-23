import axes
from time import sleep
from math import pi
import logging
import sys

def main():
    logging.info("Starting sandtrails ")
    try:
        axes.setup_steppermotors()
       
        logging.info("Steppermotor set up") 
        rho = axes.axis(axes.AXISTYPE['Rho'], -5, 100)
        theta = axes.axis(axes.AXISTYPE['Theta'], -0.1*pi, 2.1*pi)
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
            axes.GPIO.cleanup()
            logging.info("GPIO cleanup performed")

if __name__ == '__main__':
    #logging.basicConfig(filename='sandtrails.log', level=logging.INFO, format='%(levelname)s: %(message)s')
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    if sys.version_info[0] < 3:
        logging.critical("Must be using Python 3")
    else:
        main()
