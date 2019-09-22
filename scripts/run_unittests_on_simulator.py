#!/usr/bin/env python
import argparse
import logging
import os
import subprocess
import sys

_logger = logging.getLogger(__name__)
DEFAULT_LOG_LEVEL = logging.INFO
LOCAL_PYPI_INDEX = 'https://pypi.infinidat.com/simple'


class CommandFailed(Exception):
    def __init__(self, msg, rc):
        super(CommandFailed, self).__init__(msg)
        self.rc = rc


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", dest="src_dir", default='src', help="directory for source files")
    parser.add_argument("--env", dest="env_dir", default='.env', help="directory for virtuale environment")
    parser.add_argument("--python-executeable", dest="python_exec", default=None)
    parser.add_argument("--bundle-version", dest="bundle_version", required=True)
    parser.add_argument("--infinisdk-dir", dest="sdk_dir", default=None)
    parser.add_argument("--pytest-color", dest="pytest_color", default='auto')
    parser.add_argument("-v", action="append_const", const=-10, dest="verbosity", default=[])
    parser.add_argument("-q", action="append_const", const=10, dest="verbosity", default=[])
    return parser.parse_args()


def check_process(cmd, cwd=None):
    cmd_desc = "{}$ {}".format(cwd or '', cmd)
    _logger.info(cmd_desc)
    proc = subprocess.Popen(cmd, cwd=cwd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = proc.communicate()
    rc = proc.returncode
    out = out.decode('utf-8').strip()
    err = err.decode('utf-8').strip()
    _logger.info("Command returned RC: %s\nStdout:%s\nStderr:%s", rc, out, err)
    if rc != 0:
        raise CommandFailed('Command Failed with rc={}\nCommand: {}\nError:   {}'.format(rc, cmd_desc, err), rc=rc)
    return rc, out, err


def main(src_dir, env_dir, python_exec, bundle_version, sdk_dir, pytest_color, verbosity):
    log_level = sum(verbosity) + DEFAULT_LOG_LEVEL
    logging.basicConfig(stream=sys.stderr, level=log_level, format="%(message)s")

    if sdk_dir is None:
        sdk_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sdk_dir = os.path.abspath(os.path.expanduser(sdk_dir))

    itzik_kwargs = {
        'src_dir': os.path.abspath(os.path.expanduser(src_dir)),
        'env_dir': os.path.abspath(os.path.expanduser(env_dir)),
        'python_exec': python_exec or sys.executable,
        'bundle_version': bundle_version,
    }

    # Installing infinisdk's dependencies
    itzik_cmd = "itzik setup --src {src_dir} --env {env_dir} -i {python_exec} --bundle new-infra " + \
        "--bundle-version {bundle_version} --stop-git-before infinisdk --clean"
    check_process(itzik_cmd.format(**itzik_kwargs))

    # Installing infinisdk in the environment
    check_process("{}/bin/python -m pip install -i {} -e '.[testing]'".format(env_dir, LOCAL_PYPI_INDEX), cwd=sdk_dir)

    # Running unittests
    extras = '' if bundle_version == 'master' else '--disable-warnings -k "not only_latest'
    check_process("{}/bin/pytest --color {} tests {}".format(env_dir, pytest_color, extras), cwd=sdk_dir)


def entry_point():
    try:
        kwargs = vars(parse_args())
        return main(**kwargs)
    except Exception as e:  # pylint: disable=broad-except
        _logger.critical("ERROR: %s", e)
        return 1


if __name__ == '__main__':
    sys.exit(entry_point())
