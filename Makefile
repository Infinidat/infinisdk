all:
	@echo "Please specify target"
	@exit 2

customer-release:
	python scripts/build_release.py
