import shutil
import socket
from threading import Thread
import time

import os
import os.path
from radiosource.http.youtubedl import Ydl
from radiosource.meta import parse_fn
from radiosource.source import DirectorySource

SOCKET_PATH = '/tmp/radiosource.socket'

class ApiHandler(object):
    def __init__(self):
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)

        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(SOCKET_PATH)
        self.server.listen(1)

        self.thread = Thread(target=self._listen)
        self.thread.setDaemon(True)

        self.thread.start()

    def _listen(self):
        while True:
            conn = self.server.accept()[0]

            buf = ''
            while True:
                data = conn.recv(1024)
                if '\n' in data:
                    (final, rest) = data.split('\n', 1)
                    self.route(buf + final, conn)
                    break
                else:
                    buf += data

    def route(self, line, conn):
        cmdline = line.split(' ', 1)
        command = cmdline[0]
        arg = cmdline[1] if len(cmdline)>1 else None

        print 'cmd=%s, arg=%s' % (command, arg)

        handler = getattr(self, 'handle_' + command, None)
        if handler:
            try:
                response = handler(arg) if arg is not None else handler()
                if response:
                    conn.send(response + '\n')
                else:
                    conn.send('ok\n')
            except Exception as ex:
                conn.send('error '+ str(ex) + '\n')
        else:
            conn.send('not found handler\n')


class RadioApi(ApiHandler):
    def __init__(self, download_folder, source, trash_folder):
        super(RadioApi, self).__init__()
        """
        :type download_folder: str
        :type source: radiosource.DirectorySource
        :type trash: str
        """
        self.download_folder = download_folder
        self.source = source
        self.trash_folder = trash_folder

        self.ydl = Ydl(self.download_folder)

    def handle_download(self, url):
        print "Will download " + url
        self.ydl.download(url)

    def handle_next(self):
        print "Swithc to next track"
        self.source.next()

    def handle_reload(self):
        print "Reload all tracks"
        self.source.reset()

    def handle_del(self):
        print "Delete current track"
        current_track = self.source.current_track()
        print "Deleting " + current_track
        shutil.move(current_track, self.trash_folder)

    def handle_np(self):
        current_track = self.source.current_track()
        np = '-'.join(parse_fn(current_track))
        print "Now playing " + np
        return np

    def handle_add(self, local_file_path):
        print 'Adding local file ' + local_file_path
        shutil.move(local_file_path, self.download_folder)


if __name__ == '__main__':
    a = RadioApi('/tmp', DirectorySource('/tmp'), '/tmp/trash')

    time.sleep(1)

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(SOCKET_PATH)
    client.send('next\n')
    print client.recv(1024)

    client.send('np\n')
    print client.recv(1024)
    client.close()

    time.sleep(1)

    while True:
        time.sleep(1)


