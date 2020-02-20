# Import of standard packages
from time import sleep
import math
import logging          # for debug messages
import sys
import csv
import threading

# Imports for Flask
from flask import Flask, render_template, flash, redirect, url_for
from forms import SandtrailsForm

# Import of own classes
import axes

event_shutdown = threading.Event()
event_start = threading.Event()
event_stop = threading.Event()

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


def sandtrails(eShutdown, eStart, eStop):
    logging.info("Starting sandtrails ")
    try:
        axes.setup_steppermotors()
       
        logging.info("Steppermotor set up") 
        thetarho = axes.thetarho()
        thetarho.homing()
        
        while not eShutdown.isSet():
            logging.info("Waiting for start")
            sleep(1)
            if eStart.isSet():
                eStart.clear() #clear the event, not sure if this works as intended
                
                thr_coord = []
                thr_coord = parse_thr("tracks/spiral.thr")
                index = 1
                
                for coord in thr_coord:
                    logging.info("Go to " + str(round(float(coord[0]), 5)) + " " + str(round(float(coord[1])*axes.RH_MAX, 5)) + " (" + str(index) + "/" + str(len(thr_coord)) + ")")
                    thetarho.goTo([float(coord[0]), float(coord[1])*axes.RH_MAX])
                    index += 1
                    if eStop.isSet():
                        logging.info("Stop signal set, exiting pattern")
                        eStop.clear()
                        break
            
                logging.info("Pattern done!")
                
        logging.info("Main loop shutting down")
    
    except Exception as err:
        logging.error("Exception occured: " + str(err))
    finally:
        # shut down cleanly
        try: # drive axes to zero
            logging.info("Going back home")
            thetarho.stripTheta()
            thetarho.goTo([0, 0])
        except Exception as error2:
            logging.error("Exception occured: " + str(error2))
            logging.error("Could not drive axes back to zero. Careful on next run, might hit physical limits")
        finally:
            axes.GPIO.cleanup()
            logging.debug("GPIO cleanup performed")
            logging.info("Sandtrails ended. Press Ctrl+C to quit app.")

app = Flask(__name__)
app.config.from_object('config.Config')

@app.route('/', methods=('GET', 'POST'))
def index():
    formInstance = SandtrailsForm()
    if formInstance.validate_on_submit():
        flash('Starting track {}'.format(formInstance.track.data))
        return redirect(url_for('start'))
    return render_template('index.html', form=formInstance)

@app.route('/shutdown')
def shutdown():
    event_shutdown.set()
    event_start.clear()
    event_stop.clear()
    formInstance = SandtrailsForm()
    return render_template('index.html', form=formInstance)

@app.route('/start')
def start():
    event_shutdown.clear()
    event_start.set()
    event_stop.clear()
    formInstance = SandtrailsForm()
    return render_template('index.html', form=formInstance)

@app.route('/stop')
def stop():
    flash('Stopping current track')
    event_shutdown.clear()
    event_start.clear()
    event_stop.set()
    formInstance = SandtrailsForm()
    return render_template('index.html', form=formInstance)

if __name__ == '__main__':
    msgFormat = "%(asctime)s: %(levelname)s: %(message)s"
    dateFormat = "%H:%H:%S"
    #logging.basicConfig(filename='sandtrails.log', level=logging.INFO, format=msgFormat, datefmt=dateFormat)
    logging.basicConfig(level=logging.DEBUG, format=msgFormat, datefmt=dateFormat)
    if sys.version_info[0] < 3:
        logging.critical("Must use Python 3")
    else:
        
        mainThread = threading.Thread(name='sandtrailsMain', target=sandtrails, args=(event_shutdown, event_start, event_stop,))
        mainThread.start()
        logging.info("Started main sandtrails thread.")
        app.run(debug=False, host='0.0.0.0')
        mainThread.join()
        logging.info("Exited cleanly")
