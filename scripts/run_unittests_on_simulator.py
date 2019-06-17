#!/usr/bin/env python
from __future__ import print_function
import argparse
import os
import subprocess
import sys


LOCAL_PYPI_INDEX = 'https://pypi.infinidat.com/simple'

class CommandFailed(Exception):
    pass


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", dest="src_dir", default='src', help="directory for source files")
    parser.add_argument("--env", dest="env_dir", default='.env', help="directory for virtuale environment")
    parser.add_argument("--python-executeable", dest="python_exec", default=None)
    parser.add_argument("--branch-name", dest="branch_name", required=True)
    parser.add_argument("--infinisdk-dir", dest="sdk_dir", default=None)
    parser.add_argument("--pytest-color", dest="pytest_color", default='auto')
    return parser.parse_args()


def run_process(cmd, **kwargs):
    kwargs.setdefault('shell', True)
    proc = subprocess.Popen(cmd, **kwargs)
    out, err = proc.communicate()
    rc = proc.returncode
    return rc, out, err


def check_process(cmd, **kwargs):
    kwargs.setdefault('stderr', subprocess.PIPE)
    rc, out, err = run_process(cmd, **kwargs)
    if rc != 0:
        raise CommandFailed('Command Failed (rc={}): {}\nError:\n{}'.format(cmd, rc, err.decode('utf-8')))
    return out


def main(src_dir, env_dir, python_exec, branch_name, sdk_dir, pytest_color):
    if python_exec is None:
        python_exec = sys.executable
    if sdk_dir is None:
        sdk_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sdk_dir = os.path.abspath(os.path.expanduser(sdk_dir))
    env_dir = os.path.abspath(os.path.expanduser(env_dir))

    # Creating virtual environment
    check_process("{} -m virtualenv {}".format(python_exec, env_dir))

    # Cloning simulator's repositories (infinibox_sysdefs & infinisim) + installing them
    check_process("mkdir -p {}".format(src_dir))
    for repo_name in ('infinibox_sysdefs', 'infinisim'):
        check_process("git clone -b {} https://git.infinidat.com/infradev/{}.git".format(branch_name, repo_name),
                      cwd=src_dir)
        check_process("{}/bin/python -m pip install -i {} -e {}".format(env_dir, LOCAL_PYPI_INDEX, repo_name),
                      cwd=src_dir)

    # Installing infinisdk in the environment
    check_process("{}/bin/python -m pip install -i {} -e '.[testing]'".format(env_dir, LOCAL_PYPI_INDEX), cwd=sdk_dir)

    # Running unittests
    extras = '' if branch_name == 'master' else '--disable-warnings -k "not test_sphinx_doctest"'
    rc, _, _ = run_process("{}/bin/pytest --color {} tests {}".format(env_dir, pytest_color, extras), cwd=sdk_dir)
    return rc


def entry_point():
    try:
        kwargs = vars(parse_args())
        return main(**kwargs)
    except Exception as e:  # pylint: disable=broad-except
        print(str(e))
        return 1


if __name__ == '__main__':
    sys.exit(entry_point())
