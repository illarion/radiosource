import time

__author__ = 'shaman'

class Throttler(object):

    PERIOD = 1  # 1 sec

    def __init__(self, input, bitrate=128): #128 kbps

        self.speed = (bitrate*1024) / 8
        self.input = input

        self.cnt = 0
        self.t0 = None

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
            print ex
            return ''
        self.cnt += len(data)
        return data