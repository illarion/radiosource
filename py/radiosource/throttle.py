import time

import logging

__author__ = 'shaman'


class QueueReader(object):
    def __init__(self, q, on_close=None):
        """
        :type q: Queue.Queue
        """
        self.q = q
        self.buffer = []
        self.on_close=on_close

    def read(self, n=-1):
        if self.buffer:
            result = self.buffer[:n] if n > 0 else self.buffer[:]
            self.buffer = self.buffer[n:] if n > 0 else []
            return result

        data = self.q.get()

        if n <= 0:
            return data

        if len(data) > n:
            self.buffer.append(data[n:])
            return data[:n]

        return data

    def close(self):
        if self.on_close:
            self.on_close()


class Throttler(object):
    PERIOD = 1  # 1 sec

    def __init__(self, input, bitrate=128):  # 128 kbps

        self.speed = (bitrate * 1024) / 8
        self.input = input

        self.cnt = 0
        self.t0 = None
        self.log = logging.getLogger("Throttler")

    def read(self, n=-1):

        if self.t0 is None:
            self.t0 = time.time()

        if self.cnt >= self.speed:
            t1 = time.time()
            dt = t1 - self.t0

            if dt < Throttler.PERIOD:
                time.sleep(Throttler.PERIOD - dt)

            self.cnt = 0
            self.t0 = time.time()

        try:
            data = self.input.read(n)
        except IOError, ex:
            self.log.exception("I/O Error during read from source")
            return ''
        self.cnt += len(data)
        return data

    def close(self):
        self.input.close()
