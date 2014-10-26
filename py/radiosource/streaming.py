import httplib
from base64 import b64encode
import urllib
from radiosource.meta import parse_fn
from radiosource.recode import FfmpegRecoder
from radiosource.throttle import Throttler

__author__ = 'shaman'


class Streamer(object):
    def __init__(self,
                 source,
                 password,
                 icecast='localhost:8000',
                 point='/tune'):
        self.source = source
        self.password = password
        self.icecast = icecast
        self.point = point

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

        print http.getresponse().status


    def stream(self):

        http = httplib.HTTPConnection(self.icecast)
        http.connect()

        http.putrequest('SOURCE', self.point)
        http.putheader("content-type", "audio/mpeg")
        http.putheader("Authorization", 'Basic ' + b64encode('source:%s' % self.password))
        http.putheader("ice-name", "This is my server name")
        http.putheader("ice-url", "http://www.google.com")
        http.putheader("ice-genre", "DNB")
        http.putheader("ice-private", "0")
        http.putheader("ice-description", "This is my server description")
        http.putheader("ice-audio-info", "ice-samplerate=44100;ice-bitrate=128;ice-channels=2")

        http.endheaders()

        while True:
            fn = self.source.next()

            throttler = Throttler(FfmpegRecoder(fn))
            begin = throttler.read(10)

            http.send(begin)
            (artist, title) = parse_fn(fn)
            self.update_meta(artist, title)

            http.send(throttler)



