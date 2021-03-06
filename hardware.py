import logging
#import axes_nohw as axes
import axes
from time import sleep

from playlist import Status

class Hardware:
    
    def __init__(self, tracks, playlist):
        self.tracks = tracks
        self.playlist = playlist
    
    
    def run(self, eStart, eStop, eShutdown):
        logging.info("Starting sandtrails ")
        try:
            axes.setup_steppermotors()
           
            logging.info("Steppermotor set up") 
            thetarho = axes.thetarho()
            thetarho.homing()
            
            logging.info("Waiting for START")
            
            while not eShutdown.isSet():
                #logging.debug("Still waiting for START")
                sleep(1)
                if eStart.isSet():
                    eStart.clear() #clear the event, not sure if this works as intended
                    
                    while True:
                        while True:
                            thr_file = self.playlist.get_next()
                            if thr_file is None:
                                break
                            
                            thr_coord = self.tracks.parse_thr(thr_file)
                            logging.info("Starting pattern: " + thr_file)
                            axes.steppers_enable()
                            index = 1
                            
                            for coord in thr_coord:
                                #logging.info("Go to " + str(round(float(coord[0]), 5)) + " " + str(round(float(coord[1])*axes.RH_MAX, 5)) + " (" + str(index) + "/" + str(len(thr_coord)) + ")")
                                logging.info("Step " + str(index) + "/" + str(len(thr_coord)) + " (" + str(round(float(coord[0]), 5)) + " " + str(round(float(coord[1])*axes.RH_MAX, 5))  + ")")
                                thetarho.goTo([float(coord[0]), float(coord[1])*axes.RH_MAX])
                                index += 1
                                if eStop.isSet():
                                    logging.info("Stop signal set, exiting pattern")
                                    break
                            
                            thetarho.stripTheta()
                            logging.info("Pattern done!")
            
                            if eStop.isSet():
                                logging.info("Stop signal set, exiting playlist")
                                break
        
                        logging.info("Playlist done!")
                        axes.steppers_disable()
                        
                        if eStop.isSet():
                            eStop.clear()
                            break
                        
                        if self.playlist.is_looping_enabled():
                            logging.info("Playlist looping enabled. Restarting!")
                        else:
                            break
                    
                    
                    self.playlist.set_status(Status.stopped)
    
                    
            logging.info("Main loop shutting down")
        
        except Exception as err:
            logging.error("Exception occured: " + str(err))
        finally:
            # shut down cleanly
            axes.steppers_disable()
            axes.cleanup()
            logging.info("Sandtrails ended. Press Ctrl+C to quit app.")

