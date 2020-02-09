import axes
from time import sleep
import math
import logging          # for debug messages
import sys
import csv

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
        thetarho = axes.thetarho()
        thetarho.homing()
        """
        ROTATION = 2*math.pi
        thetarho.goTo([-0.1*ROTATION, 1*axes.RH_MAX])
        sleep(5)
        thetarho.goTo([0.1*ROTATION, 1*axes.RH_MAX])
        sleep(5)
        thetarho.goTo([0*ROTATION, 0.75*axes.RH_MAX])
        sleep(5)
        """
        
        thr_coord = []
        thr_coord = parse_thr("3lobes.thr")
        index = 1
        
        for coord in thr_coord:
            logging.info("Go to " + str(round(float(coord[0]), 5)) + " " + str(round(float(coord[1])*axes.RH_MAX, 5)) + " (" + str(index) + "/" + str(len(thr_coord)) + ")")
            thetarho.goTo([float(coord[0]), float(coord[1])*axes.RH_MAX])
            #sleep(1)
            index += 1
        logging.info("Pattern done!")
        
        logging.info("Main loop done")
        sleep(5)
    
    except Exception as err:
        logging.error("Exception occured: " + str(err))
    finally:
        # shut down cleanly
        try: # drive axes to zero
            logging.info("Going back home")
            sleep(2)
            thetarho.stripTheta()
            thetarho.goTo([0, 0])
        except Exception as error2:
            logging.error("Exception occured: " + str(error2))
            logging.error("Could not drive axes back to zero. Careful on next run, might hit physical limits")
        finally:
            axes.GPIO.cleanup()
            logging.info("GPIO cleanup performed")

if __name__ == '__main__':
    #logging.basicConfig(filename='sandtrails.log', level=logging.INFO, format='%(levelname)s: %(message)s')
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    if sys.version_info[0] < 3:
        logging.critical("Must use Python 3")
    else:
        main()
