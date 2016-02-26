from Queue import Queue
import random
import threading
import logging
import os

MAX_RECENT_FILES = 30

__author__ = 'shaman'


class Source(object):

    def np(self):
        pass

    def next(self):
        pass

    def reset(self):
        pass


class MultiplexingRuleSource(Source):
    def __init__(self, default_source, source_rules):
        """
        example: MultiplexingRuleSource([(source1, rule), (source2, rule2)])
        :param source_rules:
        :return:
        """
        self.default_source = default_source
        self.source_rules = source_rules

    def __find_source(self):
        for source, rule in self.source_rules:
            if rule():
                return source

        return self.default_source

    def next(self):
        return self.__find_source().next()

    def np(self):
        return self.__find_source().np()

    def reset(self):
        return self.__find_source().reset()


class DirectorySource(Source):

    def __init__(self, root, extensions=('.ogg', '.mp3')):
        self.log = logging.getLogger('DirectorySource')
        self.recent_files = []
        self.next_file = Queue(maxsize=1)
        self.current_track = None
        self.root = root
        self.extensions = extensions

        self.rescanner = threading.Thread(target=self.scan)
        self.rescanner.start()

    def scan(self):
        while True:
            scanned = set()

            for dirpath, dirnames, filenames in os.walk(self.root, followlinks=True):
                scanned.update([os.path.join(dirpath, filename)
                               for filename in filenames
                               for ext in self.extensions if filename.endswith(ext)])

            available = scanned - set(self.recent_files)

            if len(available) == 0:
                available = scanned

            next_file_index = random.randint(0, len(available)-1)
            self.next_file.put(list(available)[next_file_index])

    def np(self):
        return self.current_track

    def next(self):
        while True:
            f = self.next_file.get()

            try:
                if len(self.recent_files) > MAX_RECENT_FILES:
                    self.recent_files.pop(0)
            except IndexError:
                pass

            if os.path.exists(f):
                self.current_track = f
                self.recent_files.append(f)
                return f

    def reset(self):
        self.recent_files = []