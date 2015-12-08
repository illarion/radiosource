import sys
from StringIO import StringIO
import traceback

import datetime

import daemon
import logging

from radiosource import DEFAULT_KIND, MIX_KIND
from radiosource.api.api_handler import RadioApi
from radiosource.config import Config
from radiosource.source import DirectorySource, MultiplexingRuleSource
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

    default_folder = conf.get('main', 'files')
    mixes_folder = conf.get('main', 'files_mixes')

    default_source = DirectorySource(default_folder)
    mixes_source = DirectorySource(mixes_folder)

    kind_to_folder = {
        DEFAULT_KIND: default_folder,
        MIX_KIND: mixes_folder
    }

    def mix_rule():
        utcnow = datetime.datetime.utcnow()
        print utcnow

        return (20 <= utcnow.hour <= 23) or (0 <= utcnow.hour <= 6)


    source = MultiplexingRuleSource(default_source, [(mixes_source, mix_rule)])

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

    api_handler = RadioApi(kind_to_folder, source, streamer, conf.get('main', 'trash'))

    streamer.stream()

