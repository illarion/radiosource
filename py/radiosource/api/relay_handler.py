import SocketServer
from BaseHTTPServer import BaseHTTPRequestHandler


class Handler(BaseHTTPRequestHandler):
    def do_SOURCE(self):
        print self.headers
        self.send_response(200)




class RelayHandler(object):
    def __init__(self, bind_addr=('127.0.0.1', 9001)):
        self.httpd = SocketServer.TCPServer(("127.0.0.1", 9001), Handler)
        self.httpd.serve_forever()

if __name__ == "__main__":

    import time

    r = RelayHandler()
    while True:
        time.sleep(1)
