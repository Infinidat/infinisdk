default: test

.PHONY: doc
doc: docs

docs: env
	.env/bin/python setup.py build_sphinx -a -E

test: env
	.env/bin/py.test tests

coverage: env
	.env/bin/pip install pytest-cov
	.env/bin/py.test tests --cov=infinisdk --cov-report=html

env: .env/.up-to-date

.env/.up-to-date: setup.py Makefile
	virtualenv .env
	.env/bin/pip install -e .
	.env/bin/pip install Sphinx alabaster
	.env/bin/pip install -i http://pypi01.infinidat.com/simple -r test_requirements.txt
	touch .env/.up-to-date

develop_deps:
	virtualenv .env
	.env/bin/pip install -i http://pypi01.infinidat.com/simple -e ../ecosystem -e ../infinibox_sysdefs -e ../infinisim -e ../infinisdk_internal -e ../izsim

develop_env: develop_deps env


jenkins-docker-test:
	docker pull docker.infinidat.com/python-detox
	docker run -i -v $(CURDIR):/src docker.infinidat.com/python-detox

release: env
	.env/bin/python scripts/build_release.py
