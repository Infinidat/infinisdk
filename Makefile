default: test

test: env
	.env/bin/nosetests --with-doctest --with-coverage --cover-package infinipy2

env: .env/.up-to-date

.env/.up-to-date: setup.py Makefile
        virtualenv .env
	.env/bin/pip install -e ../izsim
	.env/bin/pip install -e .
	.env/bin/pip install nose coverage infi.unittest
	.env/bin/pip install -e git://infinigit.infinidat.com/qa/izsim#egg=izsim
	touch .env/.up-to-date

jenkins-docker-test: docker-installed
	docker pull docker.infinidat.com/python-detox
	docker run -v $(CURDIR):/src docker.infinidat.com/python-detox

docker-installed:
	curl http://docker.infinidat.com/scripts/install.sh | sh -

.PHONY: docker-installed
