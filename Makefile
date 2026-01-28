all:
	@echo "Please specify target"
	@exit 2

lint:
	pylint --rcfile .pylintrc -j $(shell nproc) infinisdk scripts tests doc/*.doctest_context

check_format:
	black --check infinisdk
	isort infinisdk --diff --check-only --profile black

do_format:
	black infinisdk
	isort infinisdk --profile black
