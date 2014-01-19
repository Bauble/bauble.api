import os
import pytest
import subprocess

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

    process = subprocess.Popen(["bake", "server", "test"], env=os.environ)
    request.addfinalizer(kill)


def pytest_exception_interact(node, call, report):
    import bauble.db
    bauble.db.engine.dispose()
