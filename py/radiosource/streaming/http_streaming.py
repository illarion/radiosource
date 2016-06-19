import httplib
import logging
import threading
import time
import urllib
from Queue import Queue, Empty
from base64 import b64encode
from threading import Thread

import os
from radiosource.codec.recoder import Recoder
from radiosource.meta import parse_fn
from radiosource.streaming import Streamer
from radiosource.throttle import Throttler, QueueReader

__author__ = 'shaman'


class MetaUpdater(object):
    def __init__(self, icecast, point, password):
        self.icecast = icecast
        self.point = point
        self.password = password

        self.log = logging.getLogger("MetaUpdater")

        self.__meta_updater = Thread(target=self.__wait_for_next_track)
        self.__meta_updater.setDaemon(True)

        self.__meta_queue = Queue()
        self.__meta_updater.start()

    def __wait_for_next_track(self):
        while True:
            track_name = self.__meta_queue.get()
            time.sleep(1)
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
                self.log.info('Unable to update metadata')
                time.sleep(1)
                self.__meta_queue.put(track_name)
            finally:
                http.close()

    def update_meta(self, track_name):
        self.__meta_queue.put(track_name)


class RecodingThread(Thread):
    def __init__(self, target_queue, blocksize, source, bitrate, meta_updater):

        self.meta_updater = meta_updater
        self.bitrate = bitrate
        self.source = source
        self.target_queue = target_queue
        self.log = logging.getLogger("RecodingThread")

        self.__next = threading.Event()
        self.__start_over_encoding = threading.Event()

        Thread.__init__(self, target=self.__in_thread, args=(target_queue, blocksize))
        self.setDaemon(True)

    def next(self):
        self.log.info("Switch to next track")
        self.__next.set()

    def start_over_encoding(self):
        self.log.info("Starting over the encoder")
        self.__start_over_encoding.set()

    def __in_thread(self, target_queue, blocksize):
        """
        :type target_queue: Queue.Queue
        :type block_size: int
        """
        recoder = Recoder(bitrate=self.bitrate)

        while True:
            fn = self.source.next()
            self.log.info("Playing %s" % fn)

            recoder.make_input_process(fn)
            data_block = recoder.read(blocksize)
            track_name = parse_fn(fn)
            self.meta_updater.update_meta(track_name)

            while os.path.exists(fn) and not self.__next.is_set():

                if data_block:
                    target_queue.put(data_block)
                try:

                    if self.__start_over_encoding.is_set():
                        self.log.info("Killing destination process in order to start over the encoder")
                        recoder.kill_dst_process()

                        self.log.info("Emptying the data queue")
                        while True:
                            try:
                                self.target_queue.get_nowait()
                            except Empty:
                                break

                        self.log.info("Finished emptying the data queue")
                        self.__start_over_encoding.clear()

                    data_block = recoder.read(blocksize)

                    if not data_block:
                        while not recoder.is_decoder_finished():
                            data_block = recoder.read(blocksize)
                            if data_block:
                                break

                    if not data_block:
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
            if self.__next.is_set():
                self.__next.clear()


class IcecastHttpStreamer(Streamer):
    def __init__(self, source, password, icecast='localhost:8000', point='/tune', bitrate=128, genre='', name='',
                 description='', url='', public=False):

        super(IcecastHttpStreamer, self).__init__(source, password, icecast, point, bitrate, genre, name, description,
                                                  url,
                                                  public)

        self.log = logging.getLogger("Streamer")

        self.__next = threading.Event()

        self.meta_updater = MetaUpdater(icecast, point, password)

    def _connect(self, retries=None):
        attempt = 1
        http = None

        while True:
            try:
                http = httplib.HTTPConnection(self.icecast, timeout=5)
                http.connect()
                break
            except Exception as ex:
                self.log.error("Unable to connect to Icecast server")
                time.sleep(1)
                attempt += 1

                try:
                    http.close()
                except:
                    pass

                if retries and attempt > retries:
                    self.log.error("Cound not establish connection in %d attempts" % retries)
                    return None

        assert http is not None
        self.log.info("Connected to icecast server after %d attempts" % attempt)

        http.putrequest('PUT', self.point)
        http.putheader("Authorization", 'Basic ' + b64encode('source:%s' % self.password))
        http.putheader("Content-type", "application/ogg")
        http.putheader("Accept", "*/*")
        http.putheader("Ice-name", self.name)
        http.putheader("Ice-url", self.url)
        http.putheader("Ice-genre", self.genre)
        http.putheader("Ice-public", "1" if self.public else "0")
        http.putheader("Ice-description", self.description)
        http.putheader("Ice-audio-info", "ice-samplerate=44100;ice-bitrate={br};ice-channels=2".format(br=self.bitrate))
        http.endheaders()

        time.sleep(0.5)

        if self.source:
            np = self.source.np()
            if np:
                track_name = parse_fn(np)
                self.meta_updater.update_meta(track_name)

        return http

    def _disconnect(self, http):
        try:
            http.close()
        except Exception, ex:
            self.log.exception("Error during closing http connection")

    def next(self):
        self.__next.set()

    def stream(self):
        blocksize = 8192
        q = Queue(maxsize=5)

        recoding_thread = RecodingThread(q, blocksize, self.source, self.bitrate, self.meta_updater)
        recoding_thread.start()

        http = None
        while True:
            queue_reader = QueueReader(q)
            throttler = Throttler(queue_reader, bitrate=self.bitrate)

            if not http:
                http = self._connect()

            datablock = throttler.read(blocksize)
            while datablock:
                if self.__next.is_set():
                    recoding_thread.next()
                    self.__next.clear()

                try:
                    http.send(datablock)
                except IOError, ex:
                    self.log.exception("I/O error during sending datablock to icecast server")
                    self._disconnect(http)

                    recoding_thread.start_over_encoding()

                    http = self._connect()
                    continue

                try:
                    datablock = throttler.read(blocksize)
                except KeyboardInterrupt as e:
                    throttler.close()
                    return
                except Exception as e:
                    self.log.exception("Error during reading from throttler")
