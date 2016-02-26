import subprocess
from unittest import TestCase

import time

from subprocess import Popen

import signal

from radiosource.codec.copystream import CopyStream


class TestCopyStream(TestCase):

    def test_set_process(self):
        a = CopyStream()

        source = Popen(['/usr/bin/cat', '/etc/passwd'], stdout=subprocess.PIPE)
        destination = Popen(['/usr/bin/cat', '-'], stdin=subprocess.PIPE)

        a.set_source_process(source)
        a.set_destination_process(destination)

        while not a.is_source_dead():
            time.sleep(0.05)

        source = Popen(['/usr/bin/cat', '/etc/services'], stdout=subprocess.PIPE)
        a.set_source_process(source)

        source.send_signal(signal.SIGTERM)
        destination.send_signal(signal.SIGTERM)

        while not a.is_source_dead():
            time.sleep(0.05)

        while not a.is_destination_dead():
            time.sleep(0.05)