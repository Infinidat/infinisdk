#! /usr/bin/python
import sys
import subprocess

if __name__ == '__main__':
    modules = ["nose", "infi.unittest", "PyYAML>=3.10", "pyforge"]
    subprocess.check_call("pip install {0}".format(" ".join(repr(m) for m in modules)), shell=True)
    subprocess.check_call("pip install git+git://gitserver.infinidat.com/qa/izsim.git@master", shell=True)
    subprocess.check_call("python setup.py develop", shell=True)
    subprocess.check_call("nosetests --with-doctest", shell=True)
