#! /usr/bin/python
import sys
import subprocess

if __name__ == '__main__':
    modules = ["nose", "infi.unittest"]
    subprocess.check_call("pip install --use-mirrors {0}".format(" ".join(modules)), shell=True)
    subprocess.check_call("python setup.py develop", shell=True)
    subprocess.check_call("nosetests -w tests", shell=True)
