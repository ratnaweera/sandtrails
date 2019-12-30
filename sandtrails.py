import axes
from time import sleep
import math
import logging          # for debug messages
import sys
import csv

RHO_MAX = 180
RHO_MIN = -5
THETA_MAX = math.inf
THETA_MIN = -math.inf

def parse_thr(thrfilename):
    logging.info("Parsing file: " + thrfilename)
    tmp_coord = []
    with open(thrfilename) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=' ')
        for row in readCSV:
            if row:
                if row[0] != "#":
                    tmp_coord.append([row[0] , row[1]]) 
    logging.info("Parsing completed")
    return(tmp_coord)

def main():
    logging.info("Starting sandtrails ")
    try:
        axes.setup_steppermotors()
       
        logging.info("Steppermotor set up") 
        rho = axes.axis(axes.AXISTYPE['Rho'], RHO_MIN, RHO_MAX)
        theta = axes.axis(axes.AXISTYPE['Theta'], THETA_MIN, THETA_MAX)
        rho.homing()
        theta.homing()
        
        thr_coord = []
        #thr_coord = parse_thr("spirale-2019-12-27.thr")
        thr_coord = parse_thr("square-2019-12-30.thr")
        index = 1
        
        for coord in thr_coord:
            logging.info("Go to " + str(coord[0]) + " " + str(coord[1]) + " (" + str(index) + "/" + str(len(thr_coord)) + ")")
            logging.info(str(float(coord[1])*RHO_MAX))
            rho.goTo(float(coord[1])*RHO_MAX)
            sleep(0.001)
            theta.goTo(float(coord[0]))
            sleep(0.001)
            index += 1
        logging.info("Pattern done!")
        sleep(1)
        theta.stripTheta()
        
        logging.info("Main loop done")
    
    except Exception as error:
        logging.error("Exception occured: " + str(error))
    finally:
        # shut down cleanly
        try: # drive axes to zero
            logging.info("Going back home")
            rho.goTo(0)
            theta.goTo(0)
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
