import logging
import sys
import traceback
from StringIO import StringIO
import daemon
from radiosource.api.api_handler import RadioApi
from radiosource.config import Config
from radiosource.source import DirectorySource
from radiosource.streaming import IcecastHttpStreamer

__author__ = 'shaman'

if __name__ == "__main__":

    debug = '--debug' in sys.argv

    logging.root.setLevel(logging.DEBUG)

    if not debug:
        daemon.daemonize('pid.txt')
        handler = logging.FileHandler('/var/log/radio.log')
    else:
        handler = logging.StreamHandler()

    formatter = logging.Formatter(fmt='%(asctime)s: (%(name)s) [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    logging.root.addHandler(handler)


    def hook(_type, _ex, _trace):
        sio = StringIO()
        traceback.print_tb(_trace, file=sio)
        logging.error("\nUncaught exception %s\nmessage='%s'\n:%s", str(_type), str(_ex), sio.getvalue())
        sio.close()
        sys.__excepthook__(_type, _ex, _trace)


    sys.excepthook = hook

    conf = Config()

    files_folder = conf.get('main', 'files')
    trash_folder = conf.get('main', 'trash')
    default_source = DirectorySource(files_folder,
                                     recent_files_storage=conf.get('main', 'recent_files_storage', '/tmp/radiorecent'))

    streamer = IcecastHttpStreamer(default_source,
                                   password=conf.get('main', 'password'),
                                   icecast=conf.get('main', 'icecast_host_port'),
                                   point=conf.get('main', 'point'),
                                   bitrate=int(conf.get('main', 'bitrate')),
                                   genre=conf.get('main', 'genre', 'Various'),
                                   name=conf.get('main', 'name', ''),
                                   description=conf.get('main', 'description', ''),
                                   url=conf.get('main', 'url', ''),
                                   public=conf.get_boolean('main', 'public', False))

    api_handler = RadioApi(default_source, streamer, files_folder, trash_folder)

    streamer.stream()
