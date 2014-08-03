import os
import shutil
from subprocess import check_call
from tempfile import mkdtemp

_REMOTE_ARCHIVES_LOCATION = '/opt/infinidat/application-repository/data/archives/'

if __name__ == "__main__":
    tmpdir = mkdtemp()

    d = {}
    with open('infinisdk/__version__.py') as f:
        exec(f, d)
    version = d['__version__']

    check_call('python setup.py sdist', shell=True)
    check_call('make doc', shell=True)
    shutil.move('./dist/infinisdk-{0}.tar.gz'.format(version), tmpdir)
    check_call('tar czvf {} ./html'.format(os.path.join(tmpdir, 'infinisdk-docs-{0}.tar.gz'.format(version))), cwd='./build/sphinx', shell=True)
    for filename in os.listdir(tmpdir):
        check_call('scp {} root@repo.infinidat.com:{}'.format(os.path.join(tmpdir, filename), _REMOTE_ARCHIVES_LOCATION), shell=True)
        check_call('ssh root@repo.infinidat.com chown app_repo:users {}/{}'.format(_REMOTE_ARCHIVES_LOCATION, filename), shell=True)
