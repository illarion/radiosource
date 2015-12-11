import shlex
import subprocess
from subprocess import Popen
import signal
import fcntl

import time

import os
from radiosource.codec.copystream import CopyStream


def prepare_cmdline(cmdline, **params):
    return shlex.split(cmdline.format(**params))


class Recoder(object):
    def __init__(self, bitrate=128):
        self.bitrate = bitrate
        self.copystream = CopyStream()
        self.src = None
        self.dst = None

        self.make_output_process()

    def make_output_process(self):
        p = Popen(prepare_cmdline('oggenc - -b {bitrate} --managed -o -', bitrate=self.bitrate),
                  stdin=subprocess.PIPE,
                  stdout=subprocess.PIPE,
                  stderr=open('/dev/null', mode='w')
                  )

        fd = p.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)  # get flags
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)  # set flags + NON_BLOCKING

        self.copystream.set_destination_process(p)
        self.dst = p

    def process_file(self, path):
        p = Popen(prepare_cmdline('ffmpeg -i "{input}" -acodec pcm_s16le -ac 2 -f wav pipe:1', input=path),
                  stdout=subprocess.PIPE, stderr=open('/dev/null', mode='w'))

        self.copystream.set_source_process(p)
        self.src = p

        return True

    def read(self, n=-1):

        try:
            return self.dst.stdout.read(n)
        except IOError as e:
            if e.errno == 11:
                time.sleep(0.2)
                return ''
            else:
                raise

    def stop(self):
        self.src.send_signal(signal.SIGTERM)

    def is_file_finished(self):
        return self.copystream.is_source_dead()

    def close(self):
        self.src.send_signal(signal.SIGKILL)
        self.dst.send_signal(signal.SIGKILL)

    def is_encoder_finished(self):
        return self.copystream.is_destination_dead()
