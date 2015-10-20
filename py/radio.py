import sys
from StringIO import StringIO
import traceback
import daemon
import logging
from radiosource.api.api_handler import RadioApi
from radiosource.config import Config
from radiosource.source import DirectorySource
from radiosource.streaming import Streamer

__author__ = 'shaman'

if __name__ == "__main__":
    debug = '--debug' in sys.argv
    if not debug:
        daemon.daemonize('pid.txt')

        filelog = logging.FileHandler('/var/log/radio.log')
        formatter = logging.Formatter(fmt='%(asctime)s: (%(name)s) [%(levelname)s] %(message)s')
        filelog.setFormatter(formatter)
        filelog.setLevel(logging.DEBUG)
        logging.root.setLevel(logging.DEBUG)
        logging.root.addHandler(filelog)

        def hook(_type, _ex, _trace):
            sio = StringIO()
            traceback.print_tb(_trace, file=sio)
            logging.error("\nUncaught exception %s\nmessage='%s'\n:%s", str(_type), str(_ex), sio.getvalue())
            sio.close()
            sys.__excepthook__(_type, _ex, _trace)

        sys.excepthook = hook

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
                        url=conf.get('main', 'url', ''),
                        public=conf.get_boolean('main', 'public', False))

    api_handler = RadioApi(conf.get('main', 'downloads'), source, streamer, conf.get('main', 'trash'))

    streamer.stream()

