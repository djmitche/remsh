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
#include "remsh.h"

static int
test_writer(int fd)
{
    remsh_xport *xp = remsh_fd_xport_new(fd);

    assert(0 == remsh_xport_write(xp, "WORDS", 5));
    assert(0 == remsh_xport_write(xp, "BOOKKEEPER", 10));
    assert(0 == remsh_xport_write(xp, "BOOKKEEPER", 10));
}

static int
test_reader(int fd)
{
    remsh_xport *xp = remsh_fd_xport_new(fd);
    char buf[256];

    assert(5 == remsh_xport_read(xp, buf, 5));
    assert(0 == strncmp(buf, "WORDS", 5));
    assert(20 == remsh_xport_read(xp, buf, sizeof(buf)));
    assert(0 == strncmp(buf, "BOOKKEEPERBOOKKEEPER", 20));
}

int main(void)
{
    int p[2];
    int parent_result, child_result;
    int status;

    if (pipe(p) < 0) {
        perror("pipe");
        return 1;
    }

    switch (fork()) {
        case -1:
            perror("fork");
            return 1;

        case 0:
            return !test_writer(p[1]);

        default:
            parent_result = test_reader(p[0]);
            if (wait(&status) < 0) {
                perror("wait");
                exit(1);
            }
            child_result = !(!WIFEXITED(status) || WEXITSTATUS(status));

            return !(child_result && parent_result);
    }
}
