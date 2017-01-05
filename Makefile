default: docs

.PHONY: doc
doc: docs

docs: env
	sphinx-build -a -E ./doc ./build/sphinx/html

customer-release: env
	python scripts/build_release.py
