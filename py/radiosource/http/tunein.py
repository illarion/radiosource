import httplib
import threading
import urllib
from Queue import Queue

import os


class TuneInUpdater(object):
    def __init__(self, station_id, partner_id, partner_key):

        self.queue = Queue()
        self.station_id = station_id
        self.partner_id = partner_id
        self.partner_key = partner_key

        self.updating_thread = threading.Thread(target=self.__in_thread)
        self.updating_thread.setDaemon(True)
        self.updating_thread.start()

    def update(self, track):
        self.queue.put(track)

    def __in_thread(self):
        while True:
            track = self.queue.get()
            track, _ = os.path.splitext(os.path.basename(track))

            artist = None
            if '-' in track:
                artist, track = (x.strip() for x in track.split('-', 1))


            params = urllib.urlencode({
                'partnerId': self.partner_id,
                'partnerKey': self.partner_key,
                'id': self.station_id,
                'title': track
            })

            if artist:
                params += '&'+urllib.urlencode({'artist': artist})

            http = httplib.HTTPConnection('air.radiotime.com', timeout=5)
            http.request('GET', '/Playing.ashx?' + params)
            http.close()

