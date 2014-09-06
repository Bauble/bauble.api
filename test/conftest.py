import os
import pytest
import subprocess
import time

process = None

os.environ['PATH'] = os.environ['PATH'] + os.pathsep + os.getcwd()

@pytest.fixture(scope="session", autouse=True)
def start_server(request):
    def kill():
        f = open('/tmp/bauble.uwsgi.fifo', 'w')
        f.write('Q')
        f.close()
        if process:
            process.kill()
    config = yaml.load(open("config.yaml"))
    environ = os.environ.copy()
    environ.update(config['test'])
    db_url = environ.get('BAUBLE_DB_URL', os.environ.get('BAUBLE_DB_URL'))
    if 'localhost' not in db_url:
        print("The tests can only be run against a local database.")
        print(db_url)
        exit(1)

    process = subprocess.Popen(["bake", "server", "test"], env=os.environ)
    time.sleep(1)
    request.addfinalizer(kill)


def pytest_exception_interact(node, call, report):
    import bauble.db
    bauble.db.engine.dispose()
