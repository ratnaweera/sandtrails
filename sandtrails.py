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
        #thetarho.goTo([math.pi, 0])
        
        thr_coord = []
        #thr_coord = parse_thr("spirale-2019-12-27.thr")
        thr_coord = parse_thr("square-2019-12-30.thr")
        index = 1
        
        for coord in thr_coord:
            logging.info("Go to " + str(coord[0]) + " " + str(float(coord[1])*axes.RH_MAX) + " (" + str(index) + "/" + str(len(thr_coord)) + ")")
            thetarho.goTo([float(coord[0]), float(coord[1])*axes.RH_MAX])
            sleep(0.001)
            index += 1
        logging.info("Pattern done!")
        sleep(1)
        thetarho.stripTheta()
        
        logging.info("Main loop done")
        sleep(2)
    
    except Exception as error:
        logging.error("Exception occured: " + str(error))
    finally:
        # shut down cleanly
        try: # drive axes to zero
            logging.info("Going back home")
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
