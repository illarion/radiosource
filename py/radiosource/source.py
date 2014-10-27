import random
import threading
from Queue import Queue
from pprint import pprint
import os

__author__ = 'shaman'


class DirectorySource(object):

    def __init__(self, root, randomize=True, rescan_period=20, extensions=('.ogg', '.mp3')):
        self._files = set()
        self.root = root
        self.randomize = randomize
        self.extensions = extensions
        self.queue = Queue()

        self.scan()
        self.rescanner = threading.Timer(rescan_period, self.scan)
        self.rescanner.start()

    def scan(self):
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

    def next(self):
        if self.queue.empty():
            self.scan()

        while True:
            f = self.queue.get()
            if os.path.exists(f):
                return f

    def __del__(self):
        try:
            self.rescanner.cancel()
        except Exception, ex:
            pass





