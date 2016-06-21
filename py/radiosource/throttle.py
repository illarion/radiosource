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
        data = b''
        pause = 1.4
        old_time_diff = 0

        t0 = None
        g0 = None

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

            yield data
            data = b''

    def close(self):
        self.input.close()
