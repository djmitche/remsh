/* This file is part of remsh
 * Copyright 2009 Dustin J. Mitchell
 * See COPYING for license information
 */

#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <assert.h>
#include <limits.h>
#include "remsh.h"

#define NUM_OPS 2

static int
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

static void
box_pprint(char *prefix, remsh_box *box)
{
    char *repr = remsh_wire_box_repr(box);
    printf("%s: %s\n", prefix, repr);
    free(repr);
}

int main(void)
{
    int p1[2], p2[2];
    remsh_xport *wxp, *rxp;
    remsh_wire *wwire, *rwire;
    int eof;
    int status;
    char my_cwd[PATH_MAX];

    if (getcwd(my_cwd, PATH_MAX) < 0) {
        perror("getcwd");
        return 1;
    }

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

        box_pprint("parent sending", box);
        assert(0 == remsh_wire_send_box(wwire, box));
        assert(0 == remsh_wire_read_box(rwire, &res));
        box_pprint("parent received", res);
        assert(1 == box_len(res));
        remsh_wire_box_extract(res, result);
        cwd = result[0].val;
        assert(cwd);

        assert(0 == strcmp(my_cwd, cwd));
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
        char my_cwd[PATH_MAX];
        remsh_box *res;

        box_pprint("parent sending", box);
        assert(0 == remsh_wire_send_box(wwire, box));
        assert(0 == remsh_wire_read_box(rwire, &res));
        box_pprint("parent rx'd", res);
        assert(1 == box_len(res));
        remsh_wire_box_extract(res, result);
        cwd = result[0].val;
        assert(cwd);

        if (getcwd(my_cwd, PATH_MAX) < 0) {
            perror("getcwd");
            return 1;
        }
        assert(0 == strcmp(my_cwd, cwd));
        printf("cwd: %s\n", cwd);
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

    return 0;
}
