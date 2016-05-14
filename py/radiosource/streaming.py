import httplib
import urllib
from Queue import Queue
from base64 import b64encode
from threading import Thread

import logging

import time

import os
from radiosource.codec.recoder import Recoder
from radiosource.meta import parse_fn
from radiosource.throttle import Throttler, QueueReader

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

        self.log = logging.getLogger("Streamer")

        self.__meta_updater = Thread(target=self.__wait_for_next_track)
        self.__meta_updater.setDaemon(True)

        self.__meta_queue = Queue()
        self.__meta_updater.start()

        self.__next = False

    def __wait_for_next_track(self):
        while True:
            track_name = self.__meta_queue.get()
            time.sleep(0.5)
            try:
                http = httplib.HTTPConnection(self.icecast)

                params = urllib.urlencode({
                    'mode': 'updinfo',
                    'mount': self.point,
                    'song': track_name
                })

                headers = {
                    "Authorization": 'Basic ' + b64encode('source:%s' % self.password),
                }

                http.request('GET', '/admin/metadata?' + params, headers=headers)
                self.log.info("Updated metadata on icecast")
            except Exception as ex:
                self.log('Unable to update metadata')
                time.sleep(1)
                self.__meta_queue.put(track_name)
            finally:
                http.close()

    def update_meta(self, track_name):
        self.__meta_queue.put(track_name)

    def _connect(self, retries=None):
        attempt = 1
        http = None

        while True:
            try:
                http = httplib.HTTPConnection(self.icecast)
                http.connect()
                break
            except Exception as ex:
                self.log.error("Unable to connect to Icecast server")
                time.sleep(1)
                attempt += 1

                if retries and attempt > retries:
                    self.log.error("Cound not establish connection in %d attempts" % retries)
                    return None

        assert http is not None
        self.log.info("Connected to icecast server after %d attempts" % attempt)

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

        if self.source:
            np = self.source.np()
            if np:
                track_name = parse_fn(np)
                self.update_meta(track_name)

        return http

    def _disconnect(self, http):
        try:
            http.close()
        except Exception, ex:
            self.log.exception("Error during closing http connection")

    def next(self):
        self.__next = True

    def __read_to_queue(self, q, block_size):
        """
        :type q: Queue.Queue
        :type block_size: int
        """
        recoder = Recoder(bitrate=self.bitrate)

        while True:
            fn = self.source.next()
            self.log.info("Playing %s" % fn)

            if recoder.is_encoder_finished():
                self.log.warn("Recreating encoder process")
                recoder.make_output_process()

            recoder.make_input_process(fn)
            data_block = recoder.read(block_size)
            track_name = parse_fn(fn)
            self.update_meta(track_name)

            while os.path.exists(fn) and not self.__next:

                if data_block:
                    q.put(data_block)
                try:
                    data_block = recoder.read(block_size)
                    if not data_block and (recoder.is_decoder_finished() or recoder.is_encoder_finished()):
                        break

                except KeyboardInterrupt as e:
                    self.log.info("got ^C, closing")
                    recoder.close()
                    return
                except Exception as e:
                    self.log.exception("Error during recoding")
                    break

            self.log.info("recoder.kill_source_process() start")
            recoder.kill_src_process()
            self.log.info("recoder.kill_source_process() done")
            if self.__next:
                self.__next = False

    def stream(self):
        blocksize = 8192

        q = Queue(maxsize=5)

        def target():
            self.__read_to_queue(q, blocksize)

        reading_thread = Thread(target=target)
        reading_thread.setDaemon(True)
        reading_thread.start()

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
                    self.log.exception("I/O error during sending datablock to icecast server")
                    self._disconnect(http)
                    http = self._connect()
                    continue

                try:
                    datablock = throttler.read(blocksize)
                except KeyboardInterrupt as e:
                    throttler.close()
                    return
                except Exception as e:
                    self.log.exception("Error during reading from throttler")
