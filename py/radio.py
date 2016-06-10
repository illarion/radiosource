import code
import datetime
import logging
import signal
import sys
import traceback
from StringIO import StringIO

import daemon
from radiosource import DEFAULT_KIND, MIX_KIND
from radiosource.api.api_handler import RadioApi
from radiosource.config import Config
from radiosource.source import DirectorySource, MultiplexingRuleSource
from radiosource.streaming import IcecastHttpStreamer


def resque(sig, frame):
    """Interrupt running process, and provide a python prompt for
    interactive debugging."""
    d = {'_frame': frame}  # Allow access to frame object.
    d.update(frame.f_globals)  # Unless shadowed by global
    d.update(frame.f_locals)

    i = code.InteractiveConsole(d)
    message = "Signal received : entering python shell.\nTraceback:\n"
    message += ''.join(traceback.format_stack(frame))
    i.interact(message)


__author__ = 'shaman'

if __name__ == "__main__":

    debug = '--debug' in sys.argv

    logging.root.setLevel(logging.DEBUG)

    if not debug:
        daemon.daemonize('pid.txt')
        handler = logging.FileHandler('/var/log/radio.log')
    else:
        handler = logging.StreamHandler()

    signal.signal(signal.SIGUSR1, resque)  # Register handler
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

    default_folder = conf.get('main', 'files')
    mixes_folder = conf.get('main', 'files_mixes')

    default_source = DirectorySource(default_folder)
    mixes_source = DirectorySource(mixes_folder)

    kind_to_folder = {
        DEFAULT_KIND: default_folder,
        MIX_KIND: mixes_folder
    }


    # def mix_rule():
    #     utcnow = datetime.datetime.utcnow()
    #     return (20 <= utcnow.hour <= 23) or (0 <= utcnow.hour <= 6)
    #source = MultiplexingRuleSource(default_source, [(mixes_source, mix_rule)])

    source = default_source

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

    api_handler = RadioApi(kind_to_folder, source, streamer, conf.get('main', 'trash'))

    streamer.stream()
