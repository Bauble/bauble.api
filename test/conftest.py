import os
import pytest
import subprocess
import time

import yaml

process = None

os.environ['PATH'] = os.environ['PATH'] + os.pathsep + os.getcwd()

@pytest.fixture(scope="session", autouse=True)
def start_server(request):
    process = None

    def kill():
        print('stopping test server...')
        if process:
            process.terminate()
            print('test server stopped.')

    config = yaml.load(open("config.yaml"))
    os.environ.update(config['test'])
    db_url = os.environ.get('BAUBLE_DB_URL')
    if 'localhost' not in db_url:
        print("The tests can only be run against a local database.")
        print(db_url)
        exit(1)

    process = subprocess.Popen("gunicorn -c gunicorn.cfg bauble",
                               env=os.environ, shell=True)
    time.sleep(1)
    request.addfinalizer(kill)


def pytest_exception_interact(node, call, report):
    import bauble.db
    bauble.db.engine.dispose()
