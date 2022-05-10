all:
	@echo "Please specify target"
	@exit 2

customer-release:
	python scripts/build_release.py


lint:
	pylint --rcfile .pylintrc -j $(shell nproc) infinisdk scripts tests doc/*.doctest_context

