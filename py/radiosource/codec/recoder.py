import shlex
import subprocess
import signal
import time
import logging

from subprocess import Popen
from radiosource.codec.copystream import CopyStream


def prepare_cmdline(cmdline, **params):
    return shlex.split(cmdline.format(**params))


class Recoder(object):
    def __init__(self, bitrate=128):
        self.log = logging.getLogger('Recoder')
        self.bitrate = bitrate
        self.copystream = CopyStream()
        self.src = None
        self.dst = None

        self.make_output_process()

    def make_output_process(self):
        try:
            log_file = open('/var/log/radio_oggenc.log', mode='w')
        except IOError:
            log_file = open('/dev/null', mode='w')

        p = Popen(prepare_cmdline('oggenc - -b {bitrate} --managed -o -', bitrate=self.bitrate),
                  stdin=subprocess.PIPE,
                  stdout=subprocess.PIPE,
                  stderr=log_file
                  )

        self.copystream.set_destination_process(p)
        self.dst = p

    def make_input_process(self, path):
        try:
            log_file = open('/var/log/radio_ffmpeg.log', mode='w')
        except IOError:
            log_file = open('/dev/null', mode='w')
        p = Popen(prepare_cmdline('ffmpeg -i "{input}" -acodec pcm_s16le -ac 2 -f wav pipe:1', input=path),
                  stdout=subprocess.PIPE, stderr=log_file)

        self.copystream.set_source_process(p)
        self.src = p

    def read(self, n=-1):
        exitcode = self.dst.poll()
        if exitcode is not None:
            self.log.warn('Output process died with %d' % exitcode)
            self.make_output_process()
            time.sleep(0.5)

        try:
            return self.dst.stdout.read(n)
        except IOError as e:
            if e.errno == 11:
                time.sleep(0.2)
            else:
                self.log.exception("I/O error while read")
            return ''
        except Exception as e:
            self.log.exception("Other error while read")
            return ''

    def kill_src_process(self):
        if self.src is not None and self.src.poll() is None:
            self.src.send_signal(signal.SIGKILL)

    def kill_dst_process(self):
        if self.dst is not None and self.dst.poll() is None:
            self.dst.send_signal(signal.SIGKILL)


    def is_decoder_finished(self):
        return self.copystream.is_source_dead()

    def is_encoder_finished(self):
        return self.copystream.is_destination_dead()

    def close(self):
        self.kill_src_process()
        self.kill_dst_process()

