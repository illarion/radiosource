from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import cgi

__author__ = 'shaman'

html = \
    """
    <html>
        <head>
            <title>Radio</title>
        </head>
        <body>
            <div>{status}</div>
            <form enctype="multipart/form-data" method='post'>
                <input type='file' name='file' />
                <input type='submit'>
            </form>
            <
            <input type="text" name="">
        </body>

    </html>
    """


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.wfile.write(html.format(status=''))

    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                     'CONTENT_TYPE': self.headers['Content-Type']})

        filename = form['file'].filename
        data = form['file'].file.read()
        open("/tmp/%s" % filename, "wb").write(data)

        self.send_response(200, "uploaded %s, thanks" % filename)
        self.wfile.write(html.format(status="uploaded %s, thanks" % filename))


class Server(object):
    def __init__(self):
        self.http_server = HTTPServer(('', 8080), Handler)


if __name__ == "__main__":
    s = Server()
    while True:
        s.http_server.handle_request()