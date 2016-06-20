import logging
import sys
import traceback
from ConfigParser import NoSectionError
from StringIO import StringIO
import daemon
from radiosource.api.api_handler import RadioApi
from radiosource.config import Config
from radiosource.http.tunein import TuneInUpdater
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

    source = DirectorySource(files_folder,
                             recent_files_storage=conf.get('main', 'recent_files_storage', '/tmp/radiorecent'))

    #tunein
    try:
        station_id = conf.get('tunein', 'station_id', None)
        partner_id = conf.get('tunein', 'partner_id', None)
        partner_key = conf.get('tunein', 'partner_key', None)

        if all((station_id, partner_key, partner_id)):
            tunein = TuneInUpdater(station_id, partner_id, partner_key)
            source.subscribe_on_next(lambda track: tunein.update(track))
    except NoSectionError:
        pass

    streamer = IcecastHttpStreamer(source,
                                   password=conf.get('main', 'password'),
                                   icecast=conf.get('main', 'icecast_host_port'),
                                   point=conf.get('main', 'point'),
                                   bitrate=int(conf.get('main', 'bitrate')),
                                   genre=conf.get('main', 'genre', 'Various'),
                                   name=conf.get('main', 'name', ''),
                                   description=conf.get('main', 'description', ''),
                                   url=conf.get('main', 'url', ''),
                                   public=conf.get_boolean('main', 'public', False))

    api_handler = RadioApi(source, streamer, files_folder, trash_folder)

    streamer.stream()
