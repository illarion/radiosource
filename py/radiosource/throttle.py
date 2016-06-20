import time
import logging
from struct import unpack, calcsize

__author__ = 'shaman'


class QueueReader(object):
    def __init__(self, q, on_close=None):
        """
        :type q: Queue.Queue
        """
        self.q = q
        self.buffer = ''
        self.on_close = on_close

    def read(self, n=-1):
        if self.buffer:
            result = self.buffer[:n] if n > 0 else self.buffer[:]
            self.buffer = self.buffer[n:] if n > 0 else ''
            return result

        data = self.q.get(block=True)

        if n <= 0:
            return data

        if len(data) > n:
            self.buffer += data[n:]
            return data[:n]

        return data

    def close(self):
        if self.on_close:
            self.on_close()


class OggsThrottler(object):
    MAGIC = b'OggS'
    PAGE_HEADER_STRUCT = '4sBBQLLLB'

    def __init__(self, input):

        self.blocksize = 1000
        self.input = input

        self.cnt = 0
        self.t0 = None
        self.g0 = None
        self.dgp_prev = 0
        self.buffer = None
        self.pause = 0

        self.log = logging.getLogger("Throttler")

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

    def parse_page_header(self, data, magic_pos):
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
        if self.pause > 0:
            time.sleep(self.pause)
            self.pause = 0

        try:
            self.pause = 0

            data = self.input.read(self.blocksize)
            position = self.find_magic(data)
            if not position:
                return data

            gp = self.parse_page_header(data, position)
            if not gp:
                return data

            current_time = time.time()
            if self.t0 is None:
                self.t0 = current_time
                self.g0 = gp
                return data

            dt = current_time - self.t0
            dgp = gp - self.g0

            if dgp < 0:
                self.t0 = current_time
                self.g0 = gp
                self.pause = 0
                self.dgp_prev = 0
                return data

            if dgp > self.dgp_prev:
                self.dgp_prev = dgp
                if dgp - dt > 0:
                    self.pause = dgp - dt

            return data

        except IOError:
            self.log.exception("I/O Error during read from source")
            return ''

    def close(self):
        self.input.close()
