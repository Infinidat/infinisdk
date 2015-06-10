default: test

.PHONY: doc
doc: docs

docs: env
	.env/bin/python setup.py build_sphinx -a -E

test: env
	.env/bin/py.test tests -n 4

coverage: env
	.env/bin/pip install pytest-cov
	.env/bin/py.test tests --cov=infinisdk --cov-report=html

env: .env/.up-to-date

.env/.up-to-date: setup.py Makefile
	virtualenv .env
	.env/bin/pip install --pre -U -e .
	.env/bin/pip install Sphinx alabaster
	.env/bin/pip install -i https://pypi.infinidat.com/simple --pre -U -r test_requirements.txt
	.env/bin/pip install -i https://pypi.infinidat.com/simple --pre -U infinisim
	touch .env/.up-to-date

.develop_deps:
	virtualenv .env
	.env/bin/pip install --pre -i http://pypi01.infinidat.com/simple -e ../ecosystem -e ../infinibox_sysdefs -e ../infinisim

develop_env: .develop_deps env


jenkins-docker-test:
	docker pull docker.infinidat.com/python-detox
	docker  run --rm -i -v $(CURDIR):/src docker.infinidat.com/python-detox tox

release: env
	.env/bin/python scripts/build_release.py
