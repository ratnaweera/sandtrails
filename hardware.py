import logging
#import axes_nohw as axes
import axes
from time import sleep
from time import perf_counter

from playlist import Status

dimLEDTimer = 10*60  # Timeout for dimming LED lights (seconds)

class Hardware:
    
    def __init__(self, tracks, playlist, lighting):
        self.tracks = tracks
        self.playlist = playlist
        self.lighting = lighting
    
    def run(self, eStart, eStop, eExit):
        logging.info("Starting sandtrails ")
        try:
            axes.setup_steppermotors()
           
            logging.info("Steppermotor set up") 
            thetarho = axes.thetarho()
            thetarho.homing()
            
            lastActive = perf_counter() 
            logging.info("Waiting for START")
            
            while not eExit.isSet():
                #logging.debug("Waiting for START")
                sleep(1)
                if perf_counter() - lastActive > dimLEDTimer:
                    logging.debug("Dimming the lights")
                    self.lighting.hw.brightness_decrease(0.05, 1)
                    lastActive = perf_counter() 

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
                                logging.debug("Go to " + str(round(float(coord[0]), 5)) + " " + str(round(float(coord[1])*axes.RH_MAX, 5)) + " (" + str(index) + "/" + str(len(thr_coord)) + ")")
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
                                lastActive = perf_counter() 
                                break
        
                        logging.info("Playlist done!")
                        lastActive = perf_counter() 
                        axes.steppers_disable()
                        
                        if eStop.isSet():
                            eStop.clear()
                            break
                        
                        if self.playlist.is_looping_enabled():
                            logging.info("Playlist looping enabled. Restarting!")
                        else:
                            break
                    
                    
                    self.playlist.set_status(Status.stopped)
                    lastActive = perf_counter() 
    
                    
            logging.debug("Exiting main loop")
        
        except Exception as err:
            logging.error("Exception occured: " + str(err))
        finally:
            # shut down cleanly
            axes.steppers_disable()
            axes.cleanup()
            self.lighting.hw.brightness_decrease(0.01, 1)
            logging.info("Sandtrails ended.")

