#pytest_plugins="test.server"

import os
import subprocess
import sys

process=None

def pytest_configure():
    print("SETUP")
    os.environ['PATH'] = os.environ['PATH'] + os.pathsep + os.getcwd()
    process = subprocess.Popen(["bake", "server", "test"], stdout=sys.stdout,
                               stderr=sys.stderr,
                               env=os.environ)

def pytest_unconfigure():
    print("UNCONFIGURE")
    if process:
        process.terminate()
