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

        self.blocksize = 8000
        self.input = input

        self.t0 = None
        self.g0 = None
        self.buffer = None

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
        data = b''
        sl = 1.4
        old_diff = 0
        while True:
            try:
                data += self.input.read(self.blocksize)
            except Exception:
                self.log.exception("Unable to read")
                continue

            position = self.find_magic(data)
            if position is None:
                continue

            gp = self.parse_page_header(data, position)
            if not gp:
                continue

            current_time = time.time()
            if self.t0 is None:
                self.reset(current_time, gp)

            dt = current_time - self.t0
            dgp = gp - self.g0

            if dgp < 0:
                print "reset"
                self.reset(current_time, gp)
                yield data
                data = b''
                continue

            cur_diff = dgp - dt
            if cur_diff > 0:
                if not old_diff:
                    old_diff = cur_diff

                if cur_diff > old_diff:
                    sl -= 0.01
                elif cur_diff < old_diff:
                    sl += 0.01

                old_diff = cur_diff

                time.sleep(sl)

            yield data
            data = b''

    def reset(self, current_time, gp):
        self.t0 = current_time
        self.g0 = gp

    def close(self):
        self.input.close()
