/* This file is part of remsh
 * Copyright 2009 Dustin J. Mitchell
 * See COPYING for license information
 */

#include <stdio.h>
#include <stdlib.h>
#include "remsh.h"
#include "testutils.h"

#include "remsh.h"

int
box_len(remsh_box *box)
{
    int l = 0;
    if (!box)
        return -1;

    while (box && box->key) {
        l++;
        box++;
    }

    return l;
}

void
box_pprint(char *prefix, remsh_box *box)
{
    char *repr = remsh_wire_box_repr(box);
    printf("%s: %s\n", prefix, repr);
    free(repr);
}

void
test_fail_call(
        const char *call,
        int rv, 
        const char *errmsg,
        const char *message,
        const char *file,
        int line)
{
    if (errmsg == NULL)
        errmsg = "(null)";
    fprintf(stderr, "%s:%d: FAILED %s\n  %s -> %d\n  error message: %s\n",
            file, line, message, call, rv, errmsg);
    exit(1);
}

void
test_fail_int(
        const char *xstr, long long int x,
        const char *ystr, long long int y,
        const char *message,
        const char *file,
        int line,
        int isnt)
{
    if (isnt)
        fprintf(stderr, "%s:%d: FAILED %s\n  got: %lld = %s\n  exp: (anything else) = %s\n",
                file, line, message, x, xstr, ystr);
    else
        fprintf(stderr, "%s:%d: FAILED %s\n  got: %lld = %s\n  exp: %lld = %s\n",
                file, line, message, x, xstr, y, ystr);

    exit(1);
}

void
test_fail_null(
        const char *xstr,
        const char *message,
        const char *file,
        int line,
        int not_null)
{
    fprintf(stderr, "%s:%d: FAILED %s\n  got: %sNULL\n",
            file, line, message, not_null? "":"non-");
    exit(1);
}

void
test_fail_str(
        const char *xstr, const char *x,
        const char *ystr, const char *y,
        const char *message,
        const char *file,
        int line)
{
    if (x == NULL)
        x = "(null)";
    if (y == NULL)
        y = "(null)";

    fprintf(stderr, "%s:%d: FAILED %s\n  got: \"%s\" = %s\n  exp: \"%s\" = %s\n",
            file, line, message, x, xstr, y, ystr);
    exit(1);
}
