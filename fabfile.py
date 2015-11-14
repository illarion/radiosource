from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project

FOLDER = 'radiosource'
__author__ = 'shaman'

from fabric.api import *


def _prepare_requirements():
    local('pip freeze > requirements.txt')


def _cleanup():
    local('rm -f requirements.txt')


def _virtualenv(command, pty=True):
    run('source ./env/bin/activate && %s' % command, pty=pty)


def stop(folder=FOLDER):
    try:
        with cd(folder):
            run('if [ -f pid.txt ]; then kill `cat pid.txt`; fi')
            run('if [ -f web_pid.txt ]; then kill `cat web_pid.txt`; fi')
            run('rm -f pid.txt')
            run('rm -f web_pid.txt')
    except:
        warn("Did not stop")


def start(folder=FOLDER, ):
    with cd(folder):
        _virtualenv('python py/radio.py', pty=False)
        _virtualenv('python py/radio_webinterface.py', pty=False)


def upload(folder=FOLDER):
    try:
        local("find ./py -name '*.pyc' -print0|xargs -0 rm", capture=False)
    except:
        warn("Nothing to delete in *.pyc")

    rsync_project(folder, local_dir='./', exclude=('env', '.gitignore', '.git', 'fabfile.py'), delete=True,)

def _mkenv(folder):
    with cd(folder):
        if not exists('env'):
            run('virtualenv env')

        _virtualenv('pip install -r requirements.txt')


def watch():
    run('tail -f /var/log/radio.log')


def deploy(folder=FOLDER):
    _prepare_requirements()
    stop(folder)
    upload(folder)
    _cleanup()
    _mkenv(folder)
    start(folder)
