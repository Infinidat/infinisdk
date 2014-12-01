#! /usr/bin/python
import sys
import subprocess

if __name__ == '__main__':
    subprocess.check_call("pip install -i http://pypi01.infinidat.com/simple -e .", shell=True)
    subprocess.check_call("pip install -i http://pypi01.infinidat.com/simple -r ./test_requirements.txt", shell=True)
    subprocess.check_call("py.test tests", shell=True)
