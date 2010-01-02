# This file is part of remsh
# Copyright 2009, 2010, 2010 Dustin J. Mitchell
# See COPYING for license information

AC_INIT([remsh], latest) # SUBST-VERSION
AM_INIT_AUTOMAKE([foreign no-define])
AC_CONFIG_SRCDIR([lib/remsh.h])
AC_CONFIG_MACRO_DIR([m4])
AC_PROG_LIBTOOL
AC_PROG_CC

## compatiblity

# replace types, if they are missing
AC_TYPE_SIZE_T
AC_TYPE_SSIZE_T

# other potentially problematic functions:
#
# malloc
# realloc
# getcwd
# memmove
# strdup
# strereror
# strtol

## generate output files

AC_CONFIG_FILES([
     Makefile
     lib/Makefile
     test/Makefile
])
AC_OUTPUT
