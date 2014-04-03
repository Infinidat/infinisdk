default: test

test: env
	.env/bin/nosetests --with-doctest

coverage: env
	.env/bin/nosetests --with-doctest --with-coverage --cover-package infinipy2

env: .env/.up-to-date

develop_env: env
	.env/bin/pip install -e ../infinisim

.env/.up-to-date: setup.py Makefile
	virtualenv .env
	.env/bin/pip install -e .
	.env/bin/pip install -r test_requirements.txt
	touch .env/.up-to-date

jenkins-docker-test:
	docker pull docker.infinidat.com/python-detox
	docker run -i -v $(CURDIR):/src docker.infinidat.com/python-detox

