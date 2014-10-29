import shlex
import time
import os

__author__ = 'shaman'

import subprocess
import threading


class Ydl(object):
    CMD = "youtube-dl -o '%(title)s.%(ext)s' --audio-quality 0 --extract-audio --audio-format vorbis \"{url}\""

    def __init__(self, download_folder):
        if not os.path.exists(download_folder):
            raise IOError("folder %s doesn't exist, no place to download" % download_folder)
        self.download_folder = download_folder
        self.processes = {}
        self.watcher = threading.Thread(target=self._cleanup)
        self.watcher.start()

    def _cleanup(self):
        while True:
            clean = []
            for url, p in self.processes.iteritems():
                p.wait()
                print "Finished downloading " + url
                clean.append(url)
            time.sleep(10)

        for url in clean:
            del self.processes[url]

    def download(self, url):
        cmd = Ydl.CMD.format(url=url)
        args = shlex.split(cmd)
        print "Downloading " + url

        process = subprocess.Popen(args, cwd=self.download_folder)
        self.processes[url] = process

    def __del__(self):
        try:
            self.watcher.cancel()
        except Exception, ex:
            pass

