/* This file is part of remsh
 * Copyright 2009 Dustin J. Mitchell
 * See COPYING for license information
 */

#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include "remsh.h"
#include "util.h"

typedef struct remsh_fd_xport {
    remsh_xport xport;
    int fd;
} remsh_fd_xport;

static int
write_impl(remsh_xport *xself, void *buf, ssize_t len)
{
    remsh_fd_xport *self = (remsh_fd_xport *)xself;

    while (len > 0) {
        ssize_t rv = write(self->fd, buf, len);
        if (rv > 0) {
            len -= rv;
            buf += rv;
        } else if (rv == 0) {
            remsh_set_errmsg(xself, strdup("write returned 0"));
            return -1;
        } else {
#ifdef EINTR
            /* retry the write on EINTR */
            if (errno == EINTR)
                continue;
#endif
            remsh_set_errmsg(xself, strdup(strerror(errno)));
            return -1;
        }
    }

    return 0;
}

static ssize_t
read_impl(remsh_xport *xself, void *buf, ssize_t len)
{
    remsh_fd_xport *self = (remsh_fd_xport *)xself;

    while (len > 0) {
        ssize_t rv = read(self->fd, buf, len);
        if (rv > 0) {
            return rv;
        } else if (rv == 0) {
            remsh_set_errmsg(xself, strdup("read returned 0"));
            return -1;
        } else {
#ifdef EINTR
            /* retry the write on EINTR */
            if (errno == EINTR)
                continue;
#endif
            remsh_set_errmsg(xself, strdup(strerror(errno)));
            return -1;
        }
    }

    return 0;
}

static int
close_impl(remsh_xport *xself)
{
    remsh_fd_xport *self = (remsh_fd_xport *)xself;
    if (self->fd >= 0) {
        if (close(self->fd) < 0) {
            remsh_set_errmsg(xself, strdup(strerror(errno)));
        }
    }
}

struct remsh_xport_vtable vtable = {
    write_impl,
    read_impl,
    close_impl
};

remsh_xport *
remsh_fd_xport_new(int fd)
{
    remsh_fd_xport *self = calloc(1, sizeof(remsh_fd_xport));
    if (!self)
        return NULL;

    self->xport.v = &vtable;
    self->xport.errmsg = NULL;
    self->fd = fd;

    return (remsh_xport *)self;
}
