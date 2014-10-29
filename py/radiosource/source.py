import random
import threading
from Queue import Queue
from pprint import pprint
import time
import os

__author__ = 'shaman'


class DirectorySource(object):

    def __init__(self, root, randomize=True, rescan_period=20, extensions=('.ogg', '.mp3')):
        self._files = set()
        self._current_track = None
        self.root = root
        self.randomize = randomize
        self.extensions = extensions
        self.queue = Queue()

        self.rescan_period = rescan_period
        self.rescanner = threading.Thread(target=self.scan)
        self.rescanner.start()

    def scan(self):
        while True:
            print "Scanning playlist..."

            if self.queue.empty():
                self._files = set()

            scanned = set()
            for dirpath, dirnames, filenames in os.walk(self.root, followlinks=True):
                scanned.update([os.path.join(dirpath, filename)
                               for filename in filenames
                               for ext in self.extensions if filename.endswith(ext)])


            new_files = scanned - self._files

            to_put = list(new_files)
            if self.randomize:
                random.shuffle(to_put)

            print 'Adding new files:'
            pprint(len(to_put))

            for file_path in to_put:
                self.queue.put(file_path)

            self._files = scanned
            time.sleep(self.rescan_period)

    def current_track(self):
        return self._current_track

    def next(self):
        while True:
            f = self.queue.get()
            if os.path.exists(f):
                self._current_track = f
                self.queue.put(f)
                return f






