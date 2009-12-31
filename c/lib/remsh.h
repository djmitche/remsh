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

/* Constructor for a transport mechanism wrapped around a simple file
 * descriptor */
remsh_xport *remsh_fd_xport_new(int fd);

/*
 * Wire Layer
 */

/* A simple array of keys and values; terminate the array with an element
 * containing a NULL key */
typedef struct remsh_box_kv {
    unsigned char key_len; /* calculated with strlen if zero */
    char *key;
    unsigned short int val_len; /* required */
    char *val;
} remsh_box_kv;

/* opaque type */
typedef struct remsh_wire remsh_wire;

/* Send a box containing they keys and values in KV_ARRAY; returns -1 on error,
 * or 0 on success. */
int remsh_wire_send_box(remsh_wire *wire, remsh_box_kv *kv_array);

/* Read a box.  The box data is stored in the wire object, and can be accessed
 * via remsh_wire_get_box_data.  Returns -1 on error and 0 on success.  The key
 * count gives the number of keys in the box, and is -1 on EOF. */
int remsh_wire_read_box(remsh_wire *wire, int *key_count);

/* Extract values from the current box.  The array specifies the keys of
 * interest; on return, any keys which were found in the most recent box
 * have the VAL and VAL_LEN attributes set.  Note that an empty value is
 * represented as a non-NULL pointer with a zero VAL_LEN.  All values are
 * zero-terminated for convenience.  The box data remains available until
 * the next call to remsh_wire_read_box or remsh_wire_send_box. */
void remsh_wire_get_box_data(remsh_wire *wire, remsh_box_kv *kv_array);

/* Constructor for remsh wires */
remsh_wire *remsh_wire_new(remsh_xport *xport);

/* Close and destroy the object; returns -1 on error, 0 on success.  The
 * object is gone and cannot be used after a successful return. */
int remsh_wire_close(remsh_wire *wire);

#endif /* REMSH_H */
