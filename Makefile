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

VERSION_FILES = doc/VERSION py/VERSION c/VERSION
$(VERSION_FILES): VERSION
	cp $< $@

version-c:
	@cd c && \
	sed 's/AC_INIT.*# SUBST-VERSION/AC_INIT([remsh], '`cat VERSION`') # SUBST-VERSION/' \
		configure.ac > tmp && \
	if cmp -s tmp configure.ac; then \
		rm tmp; \
	else \
		echo 'updated version in c/configure.ac'; \
		mv tmp configure.ac; \
	fi

AUTHORS_FILES = py/AUTHORS c/AUTHORS
$(AUTHORS_FILES): AUTHORS
	cp $< $@

COPYING_FILES = py/COPYING c/COPYING
$(COPYING_FILES): COPYING
	cp $< $@

README_FILES = py/README.txt c/README
$(README_FILES): README
	cp $< $@

common-files: $(VERSION_FILES) version-c \
	$(AUTHORS_FILES) $(COPYING_FILES) $(README_FILES)

### doc, doc-upload

doc: common-files
	cd doc && sphinx-build -E -a . html

doc-upload: common-files
	cd doc && ./doc-upload.sh

### test

test-py:
	cd py && python setup.py test

test-c:
	cd c && make check

test: test-py test-c

### dist

dist-py: common-files test-py
	cd py && python setup.py bdist_egg --dist-dir=../dist

dist-c: common-files test-c
	cd c && make distdir=../dist/remsh-`cat VERSION` top_distdir=../dist/remsh-`cat VERSION` dist

dist: dist-py dist-c
