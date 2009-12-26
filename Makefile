# This is something of a "utility" makefile, and does not build any version
# of remsh.

# Top-level targets:
# - common-files: make sure all common files (VERSION, AUTHORS, etc.) are
#   correct
# - doc: build the documentation
# - doc-upload: build the documentation and upload it to github (maintainer only)
# - test: run all tests
# - dist: make various distribution files

all: common-files

### common-files

common-files: $(VERSION_FILES)

VERSION_FILES = doc/VERSION py/VERSION
$(VERSION_FILES): VERSION
	cp $< $@

### doc, doc-upload

doc: common-files
	cd doc && sphinx-build -E -a . ../html

doc-upload: common-files
	cd doc && ./upload-docs.sh

### test

test: test-py

test-py:
	cd py && python setup.py test

### dist

dist: dist-py

dist-py: common-files test-py
	cd py && python setup.py bdist_egg --dist-dir=../dist
