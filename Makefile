all:
	@echo "Please specify target"
	@exit 2

lint:
	pylint --rcfile .pylintrc -j $(shell nproc) infinisdk scripts tests doc/*.doctest_context

