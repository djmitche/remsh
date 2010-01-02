# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information

TESTS = \
	slave-op-set-cwd \
	xport-fd \
	wire
noinst_PROGRAMS = $(TESTS)

check_LTLIBRARIES = libtestutil.la

libtestutil_la_SOURCES = \
	testutils.h \
	testutils.c

INCLUDES = -I$(top_srcdir)/lib
LDADD = $(top_builddir)/lib/libremsh.la libtestutil.la
