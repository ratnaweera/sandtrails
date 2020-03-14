import threading
from enum import Enum

Status = Enum('Status', 'running stopping stopped')

lock = threading.Lock()

class Playlist:
    def __init__(self):
        self.list = []
        self.is_looping = False
        self.status = Status.stopped

    def start_new(self, playlist, looping):
        with lock:
            self.status = Status.running
            self.list = playlist
            self.looping = looping

    def stop(self):
        with lock:
            self.status = Status.stopping

    def is_looping_enabled(self):
        return self.is_looping
    
    def length(self):
        with lock:
            return len(self.list)
    
    def get_item(self, i):
        with lock:
            return self.list[i]
        
    def set_status(self, status):
        with lock:
            self.status = status

    def get_status_string(self):
        with lock:
            return self.status.name

