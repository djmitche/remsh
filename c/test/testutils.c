/* This file is part of remsh
 * Copyright 2009, 2010, 2010 Dustin J. Mitchell
 * See COPYING for license information
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <limits.h>
#include <errno.h>
#include "remsh.h"
#include "testutils.h"
#include "remsh.h"

static char orig_wd[PATH_MAX];

void
testutil_init(void)
{
    test_is_not_null(getcwd(orig_wd, PATH_MAX),
            "get startup working dir");

    rmtree("test_tmp");

    test_call_ok(mkdir("test_tmp", 0777), strerror(errno),
            "make test_tmp directory");

    test_call_ok(chdir("test_tmp"), strerror(errno),
            "cd into test_tmp directory");
}

void
testutil_cleanup(void)
{
    test_call_ok(chdir(orig_wd), strerror(errno),
            "cd into original working directory");

    rmtree("test_tmp");
}

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
rmtree(char *topdir)
{
    /* TODO: quit shelling out and actually implement this.  THIS IS BAD!! */
    char command[PATH_MAX + 10];
    int status;

    sprintf(command, "rm -rf %s", topdir);
    status = system(command);
    if (status < 0) {
        perror("system");
        exit(1);
    } else if (status != 0) {
        fprintf(stderr, "'%s' failed\n", command);
        exit(1);
    }
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

void
test_is_errbox_(remsh_box *box, const char *exp_errtag,
        const char *message,
        const char *file,
        int line)
{
    remsh_box errbox[] = {
        { 0, "errtag", 0, NULL, },
        { 0, "error", 0, NULL, },
        { 0, NULL, 0, NULL, },
    };
    char *got_errtag, *got_error;
    remsh_wire_box_extract(box, errbox);
    got_errtag = errbox[0].val;
    got_error = errbox[1].val;

    if (got_errtag && 0 == strcmp(exp_errtag, got_errtag))
        return;

    /* this might print binary data; let's hope not */
    fprintf(stderr, "%s:%d: FAILED %s\n  exp: '%s' error box\n  got: %s\n",
            file, line, message, exp_errtag, remsh_wire_box_repr(box));
    exit(1);
}

