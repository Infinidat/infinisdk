#! /usr/bin/python
import sys
import subprocess

if __name__ == '__main__':
    modules = ["nose", "infi.unittest>=1.0.0", "pyforge"]
    subprocess.check_call("pip install {0}".format(" ".join(repr(m) for m in modules)), shell=True)
    subprocess.check_call("pip install -U git+git://gitserver.infinidat.com/qa/izsim.git@master", shell=True)
    subprocess.check_call("pip install -i http://pypi01.infinidat.com/simple -e .", shell=True)
    subprocess.check_call("nosetests --with-doctest", shell=True)
