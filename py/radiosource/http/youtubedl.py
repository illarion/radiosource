import shlex
from Queue import LifoQueue

import os

__author__ = 'shaman'

import subprocess
import threading
import logging


class Ydl(object):
    CMD = "youtube-dl --no-playlist -o '%(title)s.%(ext)s' --audio-quality 0 --extract-audio --audio-format vorbis \"{url}\""

    def __init__(self, kind_to_download_folder):
        self.kind_to_download_folder = kind_to_download_folder
        self.log = logging.getLogger('Ydl')
        self.processes = LifoQueue()
        self.watcher = threading.Thread(target=self._cleanup, args=(self.processes, self.log))
        self.log.info('Starting download watcher process')
        self.watcher.start()

    @staticmethod
    def _cleanup(processes, log):
        while True:
            log.info('Download watcher tick...')
            url, p = processes.get()

            log.info("Waiting for finishing download of " + url)
            retcode = p.wait()
            if retcode != 0:
                log.error('Something went wrong when downloading %s, return code is %d' % (url, retcode))
            log.info("Finished downloading " + url)

    def download(self, kind, url):
        cmd = Ydl.CMD.format(url=url)
        args = shlex.split(cmd)
        self.log.info("Downloading " + url)
        folder = self.kind_to_download_folder.get(kind, None)
        if not folder:
            self.log.error('Unknown folder for kind %s' % kind)
            return

        if not os.path.exists(folder):
            # noinspection PyBroadException
            try:
                os.mkdir(folder)
            except:
                self.log.error('Unable to create %s' % folder)
                return

        p = subprocess.Popen(args, cwd=folder)
        self.log.info("Started process of downloader for " + url)
        self.log.info("Pid == " + p.pid)
        self.processes.put((url, p))

    def __del__(self):
        try:
            self.watcher.cancel()
        except Exception, ex:
            pass

