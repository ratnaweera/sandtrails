# Import of standard packages
import logging
import sys
import threading
import re

# Imports for Flask
from flask import Flask, render_template, flash, redirect, request, jsonify
from werkzeug.utils import secure_filename

# Import of own classes
from tracks import Tracks
from playlist import Playlist
from hardware import Hardware
from ledconfig import LedConfig, Section
#from ledemulator import LedEmulator
from led import Leds

# Initializations
tracks = Tracks("tracks")
playlist = Playlist()
hardware = Hardware(tracks, playlist)
ledHw = Leds(64)
#ledHw = LedEmulator(64)
ledConfig = LedConfig(ledHw)

event_start = threading.Event()
event_stop = threading.Event()
event_shutdown = threading.Event()

# Creating the web server
app = Flask(__name__, template_folder=".", static_folder="assets")
app.config.from_object('config.Config')

# Definition of all the server routings

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', **get_dynamic_fields())

@app.route('/status', methods=['GET'])
def status():
    logging.debug('Request for status')
    d = dict(status=playlist.get_status_string())
    logging.debug('Status is: ' + str(d))
    return jsonify(d)

@app.route('/shutdown', methods=['GET'])
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
    playlist.start_new(newplaylist, newplaylist_looping)
    event_shutdown.clear()
    event_start.set()
    event_stop.clear()
    return render_template('index.html', **get_dynamic_fields())

@app.route('/stop', methods=['POST'])
def stop():
    logging.info('Request to stop')
    flash('Stopping current track')
    playlist.stop()
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
        tracks.store(file, secure_filename(file.filename))
    return render_template('index.html', **get_dynamic_fields())

@app.route('/lighting', methods=['POST'])
def set_lighting():
    sectionList = list()
    for key in request.form:
        m = re.match(r"led_color(\d)", key) 
        if m:
            nr = m.group(1)
            color = request.form[key]
            logging.info('Request to set lighting ' + str(nr) + ': ' + color)
            section = Section.fromHex(nr, color)
            sectionList.append(section)
    
    ledConfig.setSectionList(sectionList, True)
    
    return render_template('index.html', **get_dynamic_fields())

def get_dynamic_fields():
    sections = ledConfig.getSectionList()
    d = dict(tracks=tracks.list(), ledsections=sections)
    return d


# Starting the hardware controller loop in a new thread, then run the web server in this thread
if __name__ == '__main__':
    msgFormat = "%(asctime)s: %(levelname)s: %(message)s"
    dateFormat = "%H:%H:%S"
    #logging.basicConfig(filename='sandtrails.log', level=logging.INFO, format=msgFormat, datefmt=dateFormat)
    logging.basicConfig(level=logging.INFO, format=msgFormat, datefmt=dateFormat)
    if sys.version_info[0] < 3:
        logging.critical("Must use Python 3")
    else:
        ledConfig.init()
        mainThread = threading.Thread(name='sandtrailsMain', target=hardware.run, args=(event_start, event_stop, event_shutdown))
        mainThread.start()
        logging.info("Started main sandtrails thread.")
        app.run(debug=False, host='0.0.0.0')
        mainThread.join()
        logging.info("Exited cleanly")
