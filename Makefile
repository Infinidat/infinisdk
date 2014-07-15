default: test

.PHONY: doc
doc: docs

docs: env
	.env/bin/python setup.py build_sphinx -a -E

test: env
	.env/bin/py.test tests

coverage: env
	.env/bin/coverage run .env/bin/py.test tests

env: .env/.up-to-date

develop_env: env
	.env/bin/pip install -e ../ecosystem -e ../infinibox_sysdefs -e ../infinisim -e ../infinisdk_internal

.env/.up-to-date: setup.py Makefile
	virtualenv .env
	.env/bin/pip install -e .
	.env/bin/pip install Sphinx alabaster
	.env/bin/pip install -r test_requirements.txt
	touch .env/.up-to-date

jenkins-docker-test:
	docker pull docker.infinidat.com/python-detox
	docker run -i -v $(CURDIR):/src docker.infinidat.com/python-detox
