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
box_len(remsh_box_kv *box)
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

int main(void)
{
    int p1[2], p2[2];
    remsh_xport *wxp, *rxp;
    remsh_wire *wwire, *rwire;
    int eof;
    int status;
    char my_cwd[PATH_MAX];
    int i;

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
            for (i = 0; i < NUM_OPS; i++) {
                printf("perform\n");
                int rv = remsh_op_perform(rwire, wwire, &eof) < 0;
                printf("performed => %d, eof=%d\n", rv, eof);
                if (rv < 0 || eof)
                    return 1;
            }
            return 0;

        case -1:
            perror("fork");
            return 1;

        default:
            ; /* fall through */
    }

    rwire = remsh_wire_new(remsh_fd_xport_new(p1[0]));
    wwire = remsh_wire_new(remsh_fd_xport_new(p2[1]));
    close(p1[1]);
    close(p2[0]);

    /* return the current dir */
    {
        int keycount;
        remsh_box_kv box[] = {
            { 0, "meth", 7, "set_cwd", },
            { 0, "version", 1, "1", },
            { 0, "cwd", 0, NULL },
            { 0, NULL, 0, NULL, },
        };
        remsh_box_kv result[] = {
            { 0, "cwd", 0, NULL, },
            { 0, NULL, 0, NULL, },
        };
        char *cwd;
        remsh_box_kv *res;

        assert(0 == remsh_wire_send_box(wwire, box));
        assert(0 == remsh_wire_read_box(rwire, &res));
        assert(1 == box_len(res));
        remsh_wire_get_box_data(res, result);
        cwd = result[0].val;
        assert(cwd);

        assert(0 == strcmp(my_cwd, cwd));
    }

    /* reset to the base dir */
    {
        int keycount;
        remsh_box_kv box[] = {
            { 0, "meth", 7, "set_cwd", },
            { 0, "version", 1, "1", },
            { 0, NULL, 0, NULL, },
        };
        remsh_box_kv result[] = {
            { 0, "cwd", 0, NULL, },
            { 0, NULL, 0, NULL, },
        };
        char *cwd;
        char my_cwd[PATH_MAX];
        remsh_box_kv *res;

        printf("writing 2\n");
        assert(0 == remsh_wire_send_box(wwire, box));
        printf("reading 2\n");
        assert(0 == remsh_wire_read_box(rwire, &res));
        printf("read 2\n");
        assert(1 == box_len(res));
        remsh_wire_get_box_data(res, result);
        cwd = result[0].val;
        assert(cwd);

        if (getcwd(my_cwd, PATH_MAX) < 0) {
            perror("getcwd");
            return 1;
        }
        assert(0 == strcmp(my_cwd, cwd));
        printf("cwd: %s\n", cwd);
    }

    /* this side completed successfully, so wait for the child */
    if (wait(&status) < 0) {
        perror("wait");
        return 1;
    }

    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0)
        return 1;

    return 0;
}
