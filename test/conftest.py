#pytest_plugins="test.server"

import os
import subprocess
import sys

process=None

os.environ['PATH'] = os.environ['PATH'] + os.pathsep + os.getcwd()

def pytest_configure():
    os.environ['PATH'] = os.environ['PATH'] + os.pathsep + os.getcwd()
    global process
    process = subprocess.Popen(["bake", "server", "test"], #stdout=sys.stdout,
                               #stderr=sys.stderr,
                               env=os.environ)
    print(process.pid)

def pytest_unconfigure():
    # send the quit command created by the named pipe defined in uwsgi.ini
    f = open('/tmp/bauble.uwsgi.fifo', 'w')
    f.write('Q')
    f.close()
    global process
    if process:
        process.kill()
