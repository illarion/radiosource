import sys
import daemon
from radiosource.config import Config
from radiosource.http.index import Server
from radiosource.source import DirectorySource
from radiosource.streaming import Streamer

__author__ = 'shaman'

if __name__ == "__main__":
    debug = '--debug' in sys.argv
    if not debug:
        daemon.daemonize('pid.txt')

    conf = Config()

    source = DirectorySource(conf.get('main', 'files'))
    web_server = Server(conf.get('main', 'downloads'),
                        source,
                        conf.get('main', 'trash'),
                        conf.get('main', 'admin_login'),
                        conf.get('main', 'admin_password'))

    streamer = Streamer(source,
                        password=conf.get('main', 'password'),
                        icecast=conf.get('main', 'icecast_host_port'),
                        point=conf.get('main', 'point'),
                        bitrate=int(conf.get('main', 'bitrate')),
                        genre=conf.get('main', 'genre', 'Various'),
                        name=conf.get('main', 'name', ''),
                        description=conf.get('main', 'description', ''),
                        url=conf.get('main', 'url', ''),
                        public=conf.get_boolean('main', 'public', False))
    streamer.stream()