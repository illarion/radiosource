from radiosource.config import Config
from radiosource.source import DirectorySource
from radiosource.streaming import Streamer

__author__ = 'shaman'

if __name__ == "__main__":
    conf = Config()

    source = DirectorySource(conf.get('main', 'files'))
    streamer = Streamer(source,
                        password=conf.get('main', 'password'),
                        icecast=conf.get('main', 'icecast_host_port'),
                        point=conf.get('main', 'point'),
                        bitrate=int(conf.get('main', 'bitrate')),
                        genre=conf.get('main', 'genre', 'Various'),
                        name=conf.get('main', 'name', ''),
                        description=conf.get('main', 'description', ''),
                        url=conf.get('main', 'url', ''))
    streamer.stream()