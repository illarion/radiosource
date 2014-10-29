from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import base64
import cgi
import threading
import errno

import os
import shutil
from radiosource.http.youtubedl import Ydl
from radiosource.meta import parse_fn


__author__ = 'shaman'

style = \
    """
        body {
            font-size: 10pt;
        }
        form, fieldset { border: 0}
    """

html = \
    """
    <!DOCTYPE html>
    <html>
        <head>
            <link rel="stylesheet" href="http://yui.yahooapis.com/pure/0.5.0/pure-min.css">
            <style type="text/css">
                #STYLE#
            </style>
            <title>Radio</title>

        </head>
        <body>
            <form class="pure-form" method='post' action='/yt'>
                <fieldset>
                    <input type='text' placeholder='youtube-url' name='yt' />
                    <button type='submit' class='pure-button pure-button-primary'>Add youtube track</button>
                </fieldset>
            </form>

            <form enctype="multipart/form-data" method='post' action='/'>
                <fieldset>
                    <input type="file" name="file" />
                    <button type='submit' class='pure-button pure-button-primary'>Upload</button>
                </fieldset>
                <div>{status}</div>
            </form>

            <form method='post' action='/del'>
                <fieldset>
                    <span>NP : {np}</span>
                    <button type='submit' class='pure-button pure-button-primary'>Delete it</button>
                </fieldset>
            </form>


        </body>

    </html>
    """


def format_html(**params):
    while True:
        try:
            return html.format(**params).replace('#STYLE#', style)
        except KeyError, ke:
            param = ke.args[0]
            params[param] = ''

class Handler(BaseHTTPRequestHandler):

    def mkform(self):
        return cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                     'CONTENT_TYPE': self.headers.get('Content-Type', 'application/octet-stream')})

    def do_GET(self):

        if not self.check_auth(self.server.login,
                               self.server.password):
            return

        if not hasattr(self.server, 'cstatus'):
            self.server.cstatus = ''

        self.send_response(200)
        self.wfile.write(format_html(np='%s - %s' % parse_fn(self.server.source.current_track()),
                                     status=self.server.cstatus))

    def _POST_file(self, form):
        filename = form['file'].filename
        print "Saving " + filename
        data = form['file'].file.read()
        open(os.path.join(self.server.download_folder, filename), "wb").write(data)
        print "Saved " + filename

        self.server.cstatus = 'Uploaded ' + filename
        self.send_response(301)
        self.send_header("Location", "/")

    def _POST_youtube(self, form):
        youtube_url = form['yt'].value
        self.server.ydl.download(youtube_url)

        self.server.cstatus = 'Added youtube url ' + youtube_url
        self.send_response(301)
        self.send_header("Location", "/")

    def _POST_del(self, form):
        current_track = self.server.source.current_track()
        print "Deleting " + current_track
        shutil.move(current_track, self.server.trash)

        self.server.cstatus = 'Deleted ' + current_track
        self.send_response(301)
        self.send_header("Location", "/")

    def check_auth(self, login, password):
        auth_header = self.headers.get('Authorization', None)

        if not auth_header:
            self.send_response(401)
            self.send_header("WWW-Authenticate", "Basic realm=\"radiosource\"")
            self.end_headers()
            return False


        lp = base64.decodestring(auth_header.replace('Basic ', '')).split(':')

        if (lp[0] != login) or (lp[1] != password):
            self.send_response(401)
            self.send_header("WWW-Authenticate", "Basic realm=\"radiosource\"")
            self.end_headers()
            return False

        return True

    def do_POST(self):
        if not self.check_auth(self.server.login,
                               self.server.password):
            return

        form = self.mkform()
        if self.path == '/':
            self._POST_file(form)
        elif self.path == '/yt':
            self._POST_youtube(form)
        elif self.path == '/del':
            self._POST_del(form)


class Server(object):
    def __init__(self, download_folder, source, trash, login, password):

        try:
            os.makedirs(trash)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(trash):
                pass
            else:
                raise exc

        self.http_server = HTTPServer(('', 8080), Handler)
        self.http_server.download_folder = download_folder
        self.http_server.ydl = Ydl(download_folder)
        self.http_server.source = source
        self.http_server.trash = trash
        self.http_server.login = login
        self.http_server.password = password

        self.t = threading.Thread(target=self._serve)
        self.t.start()

    def _serve(self):
        while True:
            self.http_server.handle_request()

