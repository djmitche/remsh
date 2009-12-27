/* This file is part of remsh
 * Copyright 2009 Dustin J. Mitchell
 * See COPYING for license information
 */

#ifndef REMSH_H
#define REMSH_H

/*
 * Xport layer
 */

struct remsh_xport;

struct remsh_xport_vtable {
    /* write to the transport; returns -1 on error, or 0 on success */
    int (* write)(struct remsh_xport *self, void *buf, ssize_t len);

    /* read from the transport; returns -1 on error, 0 on EOF, and a positive
     * number on success */
    ssize_t (* read)(struct remsh_xport *self, void *buf, ssize_t len);

    /* close the connection; returns -1 on failure, 0 on success; this also
     * frees the remsh_xport object, so SELF is invalid after this method
     * returns without error. */
    int (* close)(struct remsh_xport *self);
};

typedef struct remsh_xport {
    /* pointer to functions for this instance */
    struct remsh_xport_vtable *v;

    /* error message from most recent failure */
    char *errmsg;
} remsh_xport;

/* "method" macros */
#define remsh_xport_write(o, b, l) ((o)->v->write((o),(b),(l)))
#define remsh_xport_read(o, b, l) ((o)->v->read((o),(b),(l)))
#define remsh_xport_close(o) ((o)->v->close((o)))

/* A transport mechanism wrapped around a simple file descriptor */
remsh_xport *remsh_fd_xport_new(int fd);

#endif /* REMSH_H */
