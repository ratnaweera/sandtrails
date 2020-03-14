import logging
import csv
import os

class tracks:

    def __init__(self, thrdir):
        self.dir = thrdir

    def parse_thr(self, thrfilename):
        logging.info("Parsing file: " + thrfilename)
        thrfilepath = os.path.join(self.dir, thrfilename)
        tmp_coord = []
        with open(thrfilepath) as csvfile:
            readCSV = csv.reader(csvfile, delimiter=' ')
            for row in readCSV:
                if row:
                    if row[0] != "#":
                        tmp_coord.append([row[0] , row[1]]) 
        logging.info("Parsing completed")
        return(tmp_coord)
    
    def list(self):
        return os.listdir(self.dir)
    
    def store(self, file, filename):
        filepath = os.path.join(self.dir, filename)
        file.save(filepath)
        logging.info('Successfully stored file: ' + filepath)
