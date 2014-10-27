import time

__author__ = 'shaman'

class Throttler(object):

    PERIOD = 1  # 1 sec

    def __init__(self, input, bitrate=128): #128 kbps

        self.speed = (bitrate*1024) / 8
        self.input = input
        self.cnt = 0

    def read(self, n=-1):

        if self.cnt >= self.speed:
            self.cnt = 0
            time.sleep(Throttler.PERIOD)
        try:
            data = self.input.read(n)
        except IOError, ex:
            print ex
            return ''
        self.cnt += len(data)
        return data