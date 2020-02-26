# Import of standard packages
from time import sleep
import math
import logging          # for debug messages
import sys
import csv
import threading
import os

# Imports for Flask
from flask import Flask, render_template, flash, redirect, request, url_for
from werkzeug.utils import secure_filename

# Import of own classes
import axes

event_shutdown = threading.Event()
event_start = threading.Event()
event_stop = threading.Event()

playlist = []
playlist_looping = False
lock = threading.Lock()

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
                
                lock.acquire()
                playlist_length = len(playlist)
                lock.release()
                
                while True:
                    for i in range(playlist_length):
                        lock.acquire()
                        thr_file = playlist[i]
                        lock.release()
                        
                        thr_coord = []
                        thr_coord = parse_thr(os.path.join("tracks", thr_file))
    
                        logging.info("Starting pattern: " + thr_file)
    
                        index = 1
                        
                        for coord in thr_coord:
                            logging.info("Go to " + str(round(float(coord[0]), 5)) + " " + str(round(float(coord[1])*axes.RH_MAX, 5)) + " (" + str(index) + "/" + str(len(thr_coord)) + ")")
                            thetarho.goTo([float(coord[0]), float(coord[1])*axes.RH_MAX])
                            index += 1
                            if eStop.isSet():
                                logging.info("Stop signal set, exiting pattern")
                                break
                    
                        logging.info("Pattern done!")
        
                        if eStop.isSet():
                            logging.info("Stop signal set, exiting playlist")
                            break
    
                    logging.info("Playlist done!")
                
                    if eStop.isSet():
                        eStop.clear()
                        break
                    
                    lock.acquire()
                    restart = playlist_looping
                    lock.release()
                    
                    if restart:
                        logging.info("Playlist looping enabled. Restarting!")
                    else:
                        break
                
                
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
            axes.cleanup()
            logging.debug("GPIO cleanup performed")
            logging.info("Sandtrails ended. Press Ctrl+C to quit app.")

app = Flask(__name__, template_folder=".", static_folder="assets")
app.config.from_object('config.Config')

def get_dynamic_fields():
    tracks = os.listdir("./tracks");
    d = dict(tracks=tracks)
    return d

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', **get_dynamic_fields())

@app.route('/shutdown', methods=['POST'])
def shutdown():
    logging.info('Request to shutdown')
    event_shutdown.set()
    event_start.clear()
    event_stop.clear()
    return render_template('index.html', **get_dynamic_fields())

@app.route('/start', methods=['POST'])
def start():
    newplaylist = list(filter(None, request.form['newplaylist'].split(';')))
    newplaylist_looping = request.form['loop'].lower() == "true"
    logging.info('Request to start new playlist: ' + str(newplaylist) + ', looping = ' + str(newplaylist_looping))
    flash('Starting new playlist: ' + str(newplaylist))
    global playlist
    global playlist_looping
    lock.acquire()
    playlist = newplaylist
    playlist_looping = newplaylist_looping
    lock.release()
    event_shutdown.clear()
    event_start.set()
    event_stop.clear()
    return render_template('index.html', **get_dynamic_fields())

@app.route('/stop', methods=['POST'])
def stop():
    logging.info('Request to stop')
    flash('Stopping current track')
    event_shutdown.clear()
    event_start.clear()
    event_stop.set()
    return render_template('index.html', **get_dynamic_fields())

@app.route('/upload', methods=['POST'])
def upload():
    logging.info('File upload request')
    flash('Uploading file')
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    # if user does not select a file, the browser might also submit an empty part without filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        filename = os.path.join('tracks', secure_filename(file.filename))
        file.save(filename)
        logging.info('Successfully stored file: ' + filename)
    return render_template('index.html')

@app.route('/lighting', methods=['POST'])
def set_lighting():
    lighting = request.form['light_color']
    logging.info('Request to set lighting: ' + lighting)
    flash('Setting new lighting: ' + lighting)
    return render_template('index.html', **get_dynamic_fields())

if __name__ == '__main__':
    msgFormat = "%(asctime)s: %(levelname)s: %(message)s"
    dateFormat = "%H:%H:%S"
    #logging.basicConfig(filename='sandtrails.log', level=logging.INFO, format=msgFormat, datefmt=dateFormat)
    logging.basicConfig(level=logging.INFO, format=msgFormat, datefmt=dateFormat)
    if sys.version_info[0] < 3:
        logging.critical("Must use Python 3")
    else:
        
        mainThread = threading.Thread(name='sandtrailsMain', target=sandtrails, args=(event_shutdown, event_start, event_stop,))
        mainThread.start()
        logging.info("Started main sandtrails thread.")
        app.run(debug=False, host='0.0.0.0')
        mainThread.join()
        logging.info("Exited cleanly")
