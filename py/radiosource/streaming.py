import httplib
from base64 import b64encode
import urllib
import os
from radiosource.meta import parse_fn
from radiosource.recode import FfmpegRecoder
from radiosource.throttle import Throttler

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

    def update_meta(self, artist, title):
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

    def _connect(self):
        http = httplib.HTTPConnection(self.icecast)
        http.connect()

        http.putrequest('SOURCE', self.point)
        http.putheader("content-type", "application/ogg")
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

    def _disconnect(self, http):
        try:
            http.close()
        except Exception, ex:
            print ex



    def stream(self):
        http = None
        while True:
            fn = self.source.next()

            ffmpeg_recoder = FfmpegRecoder(fn, bitrate=self.bitrate)
            throttler = Throttler(ffmpeg_recoder, bitrate=self.bitrate)

            if not http:
                http = self._connect()

            is_new = True
            blocksize = 8192
            datablock = throttler.read(blocksize)

            while datablock and os.path.exists(fn):
                try:
                    http.send(datablock)
                except IOError, ex:
                    print ex
                    self._disconnect(http)
                    http = self._connect()
                    is_new = True
                    continue
                if is_new:
                    (artist, title) = parse_fn(fn)
                    self.update_meta(artist, title)
                    is_new = False

                datablock = throttler.read(blocksize)



