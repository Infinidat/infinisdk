import glob
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

    check_call('rm -rf ./dist', shell=True)
    check_call('python setup.py sdist', shell=True)
    check_call('make doc', shell=True)
    sdist_file = os.path.join(tmpdir, 'infinisdk-{0}-python-sdist.tar.gz'.format(version))
    docs_file = os.path.join(tmpdir,  'infinisdk-{0}-python-docs.tar.gz'.format(version))
    [built_sdist_filename] = glob.glob('./dist/infinisdk-*.tar.gz')
    shutil.move(built_sdist_filename, sdist_file)
    check_call('tar czvf {} ./html'.format(docs_file), cwd='./build/sphinx', shell=True)
    for filename in (sdist_file, docs_file):
        print 'Uploading', filename
        check_call('curl -v -1 -T {0} --ftp-pasv -u app_repo:app_repo -Q "TYPE I" -Q "cwd main-unstable" "ftp://repo-v2.lab.il.infinidat.com/"'.format(filename),
                   shell=True)
