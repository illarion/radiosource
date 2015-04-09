import random
import threading
from Queue import Queue
import time
import logging
import os

__author__ = 'shaman'


class DirectorySource(object):

    def __init__(self, root, randomize=True, rescan_period=20, extensions=('.ogg', '.mp3')):
        self.log = logging.getLogger('DirectorySource')
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
            scanned = set()

            for dirpath, dirnames, filenames in os.walk(self.root, followlinks=True):
                scanned.update([os.path.join(dirpath, filename)
                               for filename in filenames
                               for ext in self.extensions if filename.endswith(ext)])

            new_files = scanned - self._files
            deleted_files = self._files - scanned
            if deleted_files:
                self.log.info('Deleted %d files' % len(deleted_files))

            self._files.update(new_files)
            self._files = self._files - deleted_files

            to_put = list(new_files)

            if self.randomize:
                random.shuffle(to_put)

            if to_put:
                self.log.info('Adding %d new files to play queue' % len(to_put))

            for file_path in to_put:
                self.queue.put(file_path)

            time.sleep(self.rescan_period)

    def current_track(self):
        return self._current_track

    def next(self):
        while True:
            f = self.queue.get()
            if os.path.exists(f):
                self._current_track = f
                self._files -= {f}  #will be found by rescan process and added
                return f






