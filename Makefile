test:
	nosetests --with-doctest --with-coverage --cover-package infinipy2

jenkins-docker-test: docker-installed
	docker pull docker.infinidat.com/python-detox
	docker run -v $(CURDIR):/src docker.infinidat.com/python-detox

docker-installed:
	curl http://docker.infinidat.com/scripts/install.sh | sh -

.PHONY: docker-installed
