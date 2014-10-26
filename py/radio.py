from radiosource.source import DirectorySource
from radiosource.streaming import Streamer

__author__ = 'shaman'

if __name__ == "__main__":
    source = DirectorySource('/home/shaman/Music/Shaman/')
    streamer = Streamer(source, 'hackme')
    streamer.stream()