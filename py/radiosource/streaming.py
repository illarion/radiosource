from Queue import Queue
import httplib
from base64 import b64encode
import urllib
import time
import os
from radiosource.meta import parse_fn
from radiosource.recode import FfmpegRecoder
from radiosource.throttle import Throttler, QueueReader
from threading import Thread

__author__ = 'shaman'


class Streamer(object):
    def __init__(self,
                 source,
                 password,
                 icecast='localhost:8000',
                 point='/tune',
                 bitrate=128,
                 genre='',
                 name='',
                 description='',
                 url='',
                 public=False):
        self.source = source
        self.password = password
        self.icecast = icecast
        self.point = point
        self.bitrate = bitrate
        self.genre = genre
        self.name = name
        self.description = description
        self.url = url
        self.public = public

        self.__meta_updater = Thread(target=self.__wait_for_next_track)
        self.__meta_updater.setDaemon(True)

        self.__meta_queue = Queue()
        self.__meta_updater.start()

        self.__next = False

    def __wait_for_next_track(self):
        while True:
            artist, title = self.__meta_queue.get()
            http = httplib.HTTPConnection(self.icecast)

            params = urllib.urlencode({
                'mode': 'updinfo',
                'mount': self.point,
                'song': '{a} - {t}'.format(a=artist, t=title)
            })

            headers = {
                "Authorization": 'Basic ' + b64encode('source:%s' % self.password),
            }

            http.request('GET', '/admin/metadata?' + params, headers=headers)
            http.close()

    def update_meta(self, artist, title):
        self.__meta_queue.put((artist, title))

    def _connect(self):
        http = httplib.HTTPConnection(self.icecast)
        http.connect()

        http.putrequest('SOURCE', self.point)
        http.putheader("content-type", "audio/ogg")
        http.putheader("Authorization", 'Basic ' + b64encode('source:%s' % self.password))
        http.putheader("ice-name", self.name)
        http.putheader("ice-url", self.url)
        http.putheader("ice-genre", self.genre)
        http.putheader("ice-private", "0" if self.public else "1")
        http.putheader("ice-public", "1" if self.public else "0")
        http.putheader("ice-description", self.description)
        http.putheader("ice-audio-info", "ice-samplerate=44100;ice-bitrate={br};ice-channels=2".format(br=self.bitrate))

        http.endheaders()
        return http

    @staticmethod
    def _disconnect(http):
        try:
            http.close()
        except Exception, ex:
            print ex

    def next(self):
        self.__next = True


    def __read_to_queue(self, q, block_size):
        """
        :type q: Queue.Queue
        :type block_size: int
        """
        while True:
            fn = self.source.next()

            ffmpeg_recoder = FfmpegRecoder(fn, bitrate=self.bitrate)
            data_block = ffmpeg_recoder.read(block_size)

            (artist, title) = parse_fn(fn)
            self.update_meta(artist, title)

            while data_block and os.path.exists(fn) and not self.__next:
                q.put(data_block)
                try:
                    data_block = ffmpeg_recoder.read(block_size)
                except KeyboardInterrupt as e:
                    ffmpeg_recoder.close()
                    return
                except Exception as e:
                    print e
                    try:
                        ffmpeg_recoder.close()
                    except:
                        pass

                    break

            if self.__next:
                ffmpeg_recoder.close()
                self.__next = False

    def stream(self):
        blocksize = 8192

        q = Queue(maxsize=5)

        def target():
            self.__read_to_queue(q, blocksize)

        reading_thread = Thread(target=target)
        reading_thread.setDaemon(True)
        reading_thread.start()

        time.sleep(2)

        http = None
        while True:
            queue_reader = QueueReader(q)
            throttler = Throttler(queue_reader, bitrate=self.bitrate)

            if not http:
                http = self._connect()

            datablock = throttler.read(blocksize)
            while datablock:
                try:
                    http.send(datablock)
                except IOError, ex:
                    print ex
                    self._disconnect(http)
                    http = self._connect()
                    continue

                try:
                    datablock = throttler.read(blocksize)
                except KeyboardInterrupt as e:
                    throttler.close()
                    return
                except Exception as e:
                    print e
