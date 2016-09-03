import pickle
from Queue import Queue
import random
import threading
import logging
import os

__author__ = 'shaman'


class Source(object):

    def __init__(self):
        super(Source, self).__init__()
        self.on_next = []

    def np(self):
        pass

    def next(self):
        pass

    def reset(self):
        pass

    def subscribe_on_next(self, callback):
        self.on_next.append(callback)


class MultiplexingRuleSource(Source):
    def __init__(self, default_source, source_rules):
        """
        example: MultiplexingRuleSource([(source1, rule), (source2, rule2)])
        :param source_rules:
        :return:
        """
        super(MultiplexingRuleSource, self).__init__()
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
    def __init__(self, root, recent_files_storage='/tmp/radiorecent'):
        super(DirectorySource, self).__init__()
        self.log = logging.getLogger('DirectorySource')
        self.recent_files_storage = recent_files_storage

        try:
            with open(recent_files_storage, 'r') as f:
                self.recent_files = pickle.load(f)
        except IOError:
            self.recent_files = []

        self.next_file = Queue(maxsize=1)
        self.current_track = None
        self.root = root

        self.rescanner = threading.Thread(target=self.scan)
        self.rescanner.start()
        self.max_recent_files = None

    def scan(self):
        while True:
            scanned = set()

            for dirpath, dirnames, filenames in os.walk(self.root, followlinks=True):
                full_paths = [os.path.join(dirpath, filename) for filename in filenames]
                scanned.update([full_path for full_path in full_paths if os.path.isfile(full_path)])

            self.max_recent_files = len(scanned) / 2

            available = scanned - set(self.recent_files)

            if len(available) == 0:
                available = scanned

            next_file_index = random.randint(0, len(available) - 1)
            self.next_file.put(list(available)[next_file_index])

    def np(self):
        return self.current_track

    def next(self):
        while True:
            f = self.next_file.get()

            try:
                while len(self.recent_files) > self.max_recent_files:
                    if self.recent_files:
                        self.recent_files.pop(0)
            except IndexError:
                pass

            self.__store_recent_files()

            if os.path.exists(f):
                self.current_track = f
                self.recent_files.append(f)
                self.__store_recent_files()

                for x in self.on_next:
                    try:
                        x(f)
                    except Exception, e:
                        self.log.exception()
                return f

    def __store_recent_files(self):
        try:
            with open(self.recent_files_storage, 'w') as f:
                pickle.dump(self.recent_files, f)
        except IOError:
            pass

    def reset(self):
        self.recent_files = []
