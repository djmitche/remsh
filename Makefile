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

VERSION_FILES = doc/VERSION py/VERSION
$(VERSION_FILES): VERSION
	cp $< $@

AUTHORS_FILES = py/AUTHORS
$(AUTHORS_FILES): AUTHORS
	cp $< $@

COPYING_FILES = py/COPYING
$(COPYING_FILES): COPYING
	cp $< $@

README_FILES = py/README.txt
$(README_FILES): README
	cp $< $@

common-files: $(VERSION_FILES) $(AUTHORS_FILES) $(COPYING_FILES) $(README_FILES)

### doc, doc-upload

doc: common-files
	cd doc && sphinx-build -E -a . html

doc-upload: common-files
	cd doc && ./doc-upload.sh

### test

test-py:
	cd py && python setup.py test

test: test-py

### dist

dist-py: common-files test-py
	cd py && python setup.py bdist_egg --dist-dir=../dist

dist: dist-py
