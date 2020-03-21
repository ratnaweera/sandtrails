import threading
from enum import Enum

Status = Enum('Status', 'running stopping stopped')

lock = threading.Lock()

class Playlist:
    def __init__(self):
        self.list = []
        self.is_looping = False
        self.status = Status.stopped
        self.i = 0

    def start_new(self, playlist, looping):
        with lock:
            self.list = playlist
            self.looping = looping
            self.status = Status.running
            self.i = 0

    def stop(self):
        with lock:
            self.status = Status.stopping

    def is_looping_enabled(self):
        return self.is_looping
    
    def get_next(self):
        """Iterates through the playlist, i.e. returns the first item when called first 
        and the next items in subsequent calls. Returns None when reaching the end of the playlist."""
        with lock:
            if self.i < len(self.list):
                item = self.list[self.i]
                self.i += 1
                return item
            else:
                return None
        
    def set_status(self, status):
        with lock:
            self.status = status

    def get_status_string(self):
        with lock:
            return self.status.name

