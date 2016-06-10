class Streamer(object):
    def __init__(self,
                 source,
                 password,
                 icecast,  # ='localhost:8000'
                 point,  # ='/tune',
                 bitrate,  # =128,
                 genre,  # ='',
                 name,  # ='',
                 description,  # , ='',
                 url,  # ='',
                 public):  # =False
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

    def stream(self):
        pass

from http_streaming import IcecastHttpStreamer
#from libshout_streaming import LibshoutStreamer
