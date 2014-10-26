import time

__author__ = 'shaman'

class Throttler(object):

    PERIOD = 1  # 1 sec

    def __init__(self, input, speed=128): #128 kbps

        self.speed = (speed*1024) / 8
        self.input = input
        self.cnt = 0

    def read(self, n=-1):

        if self.cnt >= self.speed:
            self.cnt = 0
            time.sleep(Throttler.PERIOD)

        data = self.input.read(n)
        self.cnt += len(data)
        return data