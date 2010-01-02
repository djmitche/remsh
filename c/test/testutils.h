/* This file is part of remsh
 * Copyright 2009, 2010, 2010 Dustin J. Mitchell
 * See COPYING for license information
 */

#ifndef TESTUTILS_H
#define TESTUTILS_H

#include "remsh.h"

/*
 * Setup
 */

/* call these at the beginning and end of a test program, respectively.  They set up
 * a clean filesystem for the test. */
void testutil_init(void);
void testutil_cleanup(void);

/*
 * Box Utilities
 */

/* return the number of keys in the given box, or -1 if the box is empty */
int box_len(remsh_box *box);

/* pretty-print the given box to stdout, with the given prefix */
void box_pprint(char *prefix, remsh_box *box);

/*
 * Filesystem Utilities
 */

/* remove a directory and all children - equivalent to rm -rf.  This calls
 * exit(1) on failure. */
void rmtree(char *topdir);

/*
 * Tests
 */

void test_fail_call(
        const char *call,
        int rv, 
        const char *errmsg,
        const char *message,
        const char *file,
        int line);
#define test_call_ok(CALL, ERRMSG_EXPR, MSG) \
    do { \
        int rv__ = (CALL); \
        if (rv__ < 0) test_fail_call(#CALL, rv__, ERRMSG_EXPR, MSG, __FILE__, __LINE__); \
    } while(0)

void test_fail_int(
        const char *xstr, long long int x,
        const char *ystr, long long int y, 
        const char *message,
        const char *file,
        int line,
        int isnt);
#define test_is_int(X, Y, MSG) \
    do { \
        long long int x__ = (X); long long int y__ = (Y); \
        if (x__ != y__) { \
            test_fail_int(#X, x__, #Y, y__, (MSG), __FILE__, __LINE__, 0); \
        } } while (0)
#define test_isnt_int(X, Y, MSG) \
    do { \
        long long int x__ = (X); long long int y__ = (Y); \
        if (x__ == y__) { \
            test_fail_int(#X, x__, #Y, y__, (MSG), __FILE__, __LINE__, 1); \
        } } while (0)

void test_fail_null(
        const char *xstr,
        const char *message,
        const char *file,
        int line,
        int not_null);
#define test_is_not_null(X, MSG) \
    do { \
        void *x__ = (X); \
        if (!x__) { \
            test_fail_null(#X, (MSG), __FILE__, __LINE__, 1); \
        } } while (0)
#define test_is_null(X, MSG) \
    do { \
        void *x__ = (X); \
        if (x__) { \
            test_fail_null(#X, (MSG), __FILE__, __LINE__, 0); \
        } } while (0)

void test_fail_str(
        const char *xstr, const char *x,
        const char *ystr, const char *y,
        const char *message,
        const char *file,
        int line);
#define test_is_str(X, Y, MSG) \
    do { \
        const char *x = (X); const char *y = (Y); \
        if (!x || !y || 0 != strcmp(x, y)) { \
            test_fail_str(#X, (X), #Y, (Y), (MSG), __FILE__, __LINE__); \
        } } while (0)

/* ensure that the box is an error and has the appropriate errtag */
void test_is_errbox_(remsh_box *box, const char *exp_errtag,
        const char *message,
        const char *file,
        int line);
#define test_is_errbox(B, E, M) \
    test_is_errbox_((B), (E), (M), __FILE__, __LINE__)

#endif
