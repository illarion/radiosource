import socket
import daemon
import flask
import os
from flask import Flask, render_template, request, Response
from werkzeug.utils import secure_filename, redirect
from functools import wraps
from radiosource import config
from gevent.wsgi import WSGIServer
import sys

reload(sys)
sys.setdefaultencoding("utf-8")

_MB = 1024 * 1024
SOCKET_PATH = '/tmp/radiosource.socket'


class RadioClient(object):
    def _before(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(SOCKET_PATH)

    def _after(self):
        self.sock.close()

    def download(self, url):
        self._before()
        self.sock.send('download %s\n' % url)
        result = self.sock.recv(1024)
        self._after()
        return result

    def next(self):
        self._before()
        self.sock.send('next\n')
        result = self.sock.recv(1024)
        self._after()
        return result

    def del_(self):
        self._before()
        self.sock.send('del\n')
        result = self.sock.recv(1024)
        self._after()
        return result

    def np(self):
        self._before()
        self.sock.send('np\n')
        result = self.sock.recv(1024)
        self._after()
        return result

    def add(self, local_file_path):
        self._before()
        self.sock.send('add %s\n' % local_file_path)
        result = self.sock.recv(1024)
        self._after()
        return result


client = RadioClient()
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 120 * _MB

cfg = config.Config()


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == cfg.get('main', 'admin_login') and password == cfg.get('main', 'admin_password')


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


@app.route("/", methods=['GET'])
@requires_auth
def index():
    np = client.np()
    return render_template('index.html', np=np)


@app.route("/np", methods=['GET'])
def np():
    resp = flask.Response(client.np())
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route("/upload", methods=['POST'])
@requires_auth
def upload():
    f = request.files['file']

    if f:
        filename = secure_filename(f.filename)
        local_file_path = os.path.join('/tmp/', filename)
        f.save(local_file_path)
        client.add(local_file_path)
        return redirect("/")


@app.route('/download', methods=['POST'])
@requires_auth
def download_url():
    url = request.form['url']
    client.download(url)
    return redirect("/")


@app.route('/del', methods=['POST'])
@requires_auth
def del_np():
    client.del_()
    return redirect("/")


@app.route('/next', methods=['POST'])
@requires_auth
def next():
    client.next()
    return redirect("/")


if __name__ == "__main__":
    debug = '--debug' in sys.argv
    if not debug:
        daemon.daemonize('web_pid.txt')

        http_server = WSGIServer(('', 5000), app)
        http_server.serve_forever()
    else:
        app.run(debug=True)
