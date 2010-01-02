/* This file is part of remsh
 * Copyright 2009, 2010, 2010 Dustin J. Mitchell
 * See COPYING for license information
 */

#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <limits.h>
#include "remsh.h"
#include "testutils.h"

int main(void)
{
    int p1[2], p2[2];
    remsh_xport *wxp, *rxp;
    remsh_wire *wwire, *rwire;
    int eof;
    int status;
    char my_cwd[PATH_MAX];

    testutil_init();

    test_is_not_null(getcwd(my_cwd, PATH_MAX),
            "get test directory");

    if (pipe(p1) < 0 || pipe(p2) < 0) {
        perror("pipe");
        return 1;
    }

    /* fork the slave */
    switch (fork()) {
        case 0:
            rwire = remsh_wire_new(remsh_fd_xport_new(p2[0]));
            wwire = remsh_wire_new(remsh_fd_xport_new(p1[1]));
            close(p2[1]);
            close(p1[0]);

            remsh_op_init();

            eof = 0;
            while (1) {
                int rv = remsh_op_perform(rwire, wwire, &eof);
                if (rv < 0)
                    return 1;
                if (eof) {
                    return 0;
                }
            }
            return 0;

        case -1:
            perror("fork");
            return 1;

        default:
            ; /* fall through */
    }

    rwire = remsh_wire_new(rxp = remsh_fd_xport_new(p1[0]));
    wwire = remsh_wire_new(wxp = remsh_fd_xport_new(p2[1]));
    close(p1[1]);
    close(p2[0]);

    /* return the current dir */
    {
        int keycount;
        remsh_box box[] = {
            { 0, "meth", 7, "set_cwd", },
            { 0, "version", 1, "1", },
            { 0, "cwd", 0, NULL },
            { 0, NULL, 0, NULL, },
        };
        remsh_box result[] = {
            { 0, "cwd", 0, NULL, },
            { 0, NULL, 0, NULL, },
        };
        char *cwd;
        remsh_box *res;

        test_call_ok(remsh_wire_send_box(wwire, box), NULL,
                "send box");
        test_call_ok(remsh_wire_read_box(rwire, &res), NULL,
                "read response");
        test_is_int(box_len(res), 1,
                "response has one key");
        remsh_wire_box_extract(res, result);
        test_is_str(result[0].val, my_cwd,
                "and it is cwd and has the right value");
    }

    /* enter a nonexistent directory */
    {
        int keycount;
        remsh_box box[] = {
            { 0, "meth", 7, "set_cwd", },
            { 0, "version", 1, "1", },
            { 0, "cwd", 14, "does/not/exist" },
            { 0, NULL, 0, NULL, },
        };
        remsh_box *res;

        test_call_ok(remsh_wire_send_box(wwire, box), NULL,
                "send box");
        test_call_ok(remsh_wire_read_box(rwire, &res), NULL,
                "read response");
        test_is_errbox(res, "notfound",
                "returns 'notfound' for nonexistent directory");
    }

    /* enter an existing directory */
    {
        int keycount;
        remsh_box box[] = {
            { 0, "meth", 7, "set_cwd", },
            { 0, "version", 1, "1", },
            { 0, "cwd", 6, "exists" },
            { 0, NULL, 0, NULL, },
        };
        remsh_box result[] = {
            { 0, "cwd", 0, NULL, },
            { 0, NULL, 0, NULL, },
        };
        char *expected;
        remsh_box *res;

        test_call_ok(mkdir("exists", 0777), strerror(errno),
                "make test directory");
        expected = malloc(strlen(my_cwd) + 7 + 1);
        sprintf(expected, "%s/exists", my_cwd);

        test_call_ok(remsh_wire_send_box(wwire, box), NULL,
                "send box");
        test_call_ok(remsh_wire_read_box(rwire, &res), NULL,
                "read response");
        remsh_wire_box_extract(res, result);
        test_is_str(result[0].val, expected,
                "new directory is correct");
        free(expected);
    }

    /* reset to the base dir */
    {
        int keycount;
        remsh_box box[] = {
            { 0, "meth", 7, "set_cwd", },
            { 0, "version", 1, "1", },
            { 0, NULL, 0, NULL, },
        };
        remsh_box result[] = {
            { 0, "cwd", 0, NULL, },
            { 0, NULL, 0, NULL, },
        };
        char *cwd;
        remsh_box *res;

        test_call_ok(remsh_wire_send_box(wwire, box), NULL,
                "send box");
        test_call_ok(remsh_wire_read_box(rwire, &res), NULL,
                "read response");
        test_is_int(box_len(res), 1,
                "response has one key");
        remsh_wire_box_extract(res, result);
        test_is_str(result[0].val, my_cwd,
                "and it is cwd and has the right value");
    }

    /* send EOF to the child */
    remsh_xport_close(rxp);
    remsh_xport_close(wxp);

    /* this side completed successfully, so wait for the child */
    if (wait(&status) < 0) {
        perror("wait");
        return 1;
    }

    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) {
        printf("child did not exit cleanly: %d\n", WEXITSTATUS(status));
        return 1;
    }

    testutil_cleanup();
    return 0;
}
