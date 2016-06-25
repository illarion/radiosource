import time
import logging
from struct import unpack, calcsize

__author__ = 'shaman'


class SimpleThrottler(object):
    PERIOD = 1  # 1 sec

    def __init__(self, input, bitrate=128):  # 128 kbps

        self.speed = (bitrate * 1000) / 8
        self.input = input

        self.cnt = 0
        self.t0 = None
        self.log = logging.getLogger("Throttler")

    def read(self, n=None):
        if n is None:
            n=self.speed

        if self.t0 is None:
            self.t0 = time.time()

        if self.cnt >= self.speed:
            t1 = time.time()
            dt = t1 - self.t0

            if dt < SimpleThrottler.PERIOD:
                time.sleep(SimpleThrottler.PERIOD - dt)

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


class OggsThrottler(object):
    MAGIC = b'OggS'
    PAGE_HEADER_STRUCT = '4sBBqLLLB'

    def __init__(self, input):

        self.blocksize = 8000
        self.input = input
        self.log = logging.getLogger("Throttler")
        self.generator = self.read_generator()

    def find_magic(self, data):
        """
        :type data: str
        :param data:
        :return:
        """
        p = data.find(OggsThrottler.MAGIC)
        if p == -1:
            return None

        return p

    def get_granule_position(self, data, magic_pos):
        """

        :type magic_pos: int
        :type data: str
        :param data:
        :param magic_pos:
        :return:
        """
        try:
            _, version, header_type, g_pos, bsn, psqn, crc, page_segments = unpack(OggsThrottler.PAGE_HEADER_STRUCT,
                                                                                   data[magic_pos:magic_pos + calcsize(
                                                                                       OggsThrottler.PAGE_HEADER_STRUCT)])
            return g_pos
        except:
            return None


    def read(self):
        return self.generator.next()

    def read_generator(self):
        data = b''
        pause = 1.4
        old_time_diff = 0

        t0 = None
        g0 = None

        old_granule_since_start = 0

        while True:
            try:
                data += self.input.read(self.blocksize)
            except Exception:
                self.log.exception("Unable to read")
                continue

            oggs_header_offset = self.find_magic(data)
            if oggs_header_offset is None:
                continue

            granule_position = self.get_granule_position(data, oggs_header_offset)
            if not granule_position:
                continue

            current_time = time.time()
            if t0 is None:
                t0 = current_time
                g0 = granule_position

            time_since_start = current_time - t0
            granule_since_start = granule_position - g0

            if granule_since_start < 0:
                t0 = current_time
                g0 = granule_position
                yield data
                data = b''
                continue

            if granule_since_start != old_granule_since_start:
                time_diff = granule_since_start - time_since_start
                if time_diff > 0:
                    if not old_time_diff:
                        old_time_diff = time_diff

                    if time_diff > old_time_diff:
                        pause -= 0.01
                    elif time_diff < old_time_diff:
                        pause += 0.01

                    old_time_diff = time_diff

                    time.sleep(pause)

            old_granule_since_start = granule_since_start

            yield data
            data = b''

    def close(self):
        self.input.close()
