from threading import Thread, Event
import fcntl

import logging

import time

import os


class CopyStream(object):
    def __init__(self, bufsize=1024*8):
        self.log = logging.getLogger('CopyStream')
        self.bufsize = bufsize

        self._source_ready = Event()
        self._destination_ready = Event()

        self._source_gone = Event()
        self._destination_gone = Event()

        self.source = None
        self.destination = None

        self.worker = Thread(target=self.__work)
        self.worker.setDaemon(True)
        self.worker.start()

    def __work(self):
        while True:
            self._source_ready.wait()
            self._source_gone.clear()
            self._destination_ready.wait()
            self._destination_gone.clear()

            # now we should have both processes set
            src = self.source.stdout
            dst = self.destination.stdin
            data = ''

            try:
                poll = self.source.poll()

                data = ''
                if poll is None:
                    data = src.read(self.bufsize)

                if poll is not None:
                    self.log.info("source died")
                    data = src.read()
                    self.log.info("read remains")
                    self._source_ready.clear()
                    self._source_gone.set()

            except IOError as e:
                if e.errno == 11:
                    time.sleep(0.2)
                    continue
            except Exception as e:
                self.log.exception("Error when tried to read from source process")
                self._source_ready.clear()
                self._source_gone.set()
                continue

            try:
                poll = self.destination.poll()
                if poll is not None:
                    self._destination_gone.set()
                    self._destination_ready.clear()
                    continue

                dst.write(data)
            except IOError as e:
                self.log.info("Destination process is not consuming data")
                self._destination_gone.set()
                self._destination_ready.clear()
            except Exception as e:
                self.log.exception("Other error when tried to write to destination process")
                self._destination_gone.set()
                self._destination_ready.clear()

    def set_source_process(self, process):
        fd = process.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)  # get flags
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)  # set flags + NON_BLOCKING

        self.source = process
        self._source_ready.set()

    def set_destination_process(self, process):
        self._destination_ready.clear()

        fd = process.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)  # get flags
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)  # set flags + NON_BLOCKING

        self.destination = process
        self._destination_ready.set()

    def is_source_dead(self):
        return self._source_gone.isSet()

    def is_destination_dead(self):
        return self._destination_gone.isSet()
