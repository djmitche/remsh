/* This file is part of remsh
 * Copyright 2009, 2010, 2010 Dustin J. Mitchell
 * See COPYING for license information
 */

#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include "remsh.h"
#include "util.h"

struct remsh_wire {
    remsh_xport *xport;

    /* incoming bytes */
    unsigned char *buf;
    size_t buf_start, buf_len, buf_size;

    /* current box */
    remsh_box *box;
    int box_size, box_len;
    size_t box_bytes; /* box bytes in buf used so far */
};

int remsh_wire_send_box(remsh_wire *wire, remsh_box *box)
{
    remsh_box *iter;
    unsigned short int uint16;

    /* fix key lengths befor sending anything */
    for (iter = box; iter->key; iter++) {
        if (iter->key_len == 0) {
            int key_len = strlen(iter->key);
            if (!key_len || key_len > 255)
                return -1; /* invalid key_len */
            else
                iter->key_len = (unsigned char)key_len;
        }
    }

    /* TODO: this is *horribly* inefficient - can we use writev somehow, or
     * should this code buffer smaller things into larger writes? */
    for (iter = box; iter->key; iter++) {
        uint16 = htons(iter->key_len);
        if (remsh_xport_write(wire->xport, &uint16, 2) < 0)
            return -1; /* xport error */
        if (remsh_xport_write(wire->xport, iter->key, iter->key_len) < 0)
            return -1; /* xport error */

        uint16 = htons(iter->val_len);
        if (remsh_xport_write(wire->xport, &uint16, 2) < 0)
            return -1; /* xport error */
        if (remsh_xport_write(wire->xport, iter->val, iter->val_len) < 0)
            return -1; /* xport error */
    }

    /* box terminator */
    uint16 = 0;
    if (remsh_xport_write(wire->xport, &uint16, 2) < 0)
        return -1;

    return 0;
}

int remsh_wire_read_box(remsh_wire *wire, remsh_box **box)
{
    /* invalidate the current box */
    wire->box_len = 0;
    wire->buf_start += wire->box_bytes;
    wire->buf_len -= wire->box_bytes;
    wire->box_bytes = 0;

    if (box)
        *box = NULL;

    while (1) {
        int box_invalid;
        ssize_t bytes;

        /* first, see if we can stitch together a box from the data we have */
        while (1) {
            unsigned short int key_len, val_len;
            size_t offset;

            if (wire->box_bytes + 2 > wire->buf_len)
                break;
            offset = wire->buf_start + wire->box_bytes;
            if (wire->buf[offset] != 0)
                return -1; /* invalid character in stream */
            key_len = wire->buf[offset + 1];
            if (key_len > 0) {
                if (wire->box_bytes + 2 + key_len + 2 > wire->buf_len)
                    break;
                offset = wire->buf_start + wire->box_bytes + 2 + key_len;
                val_len = (wire->buf[offset] << 8)
                       + (wire->buf[offset + 1]);
                if (wire->box_bytes + 2 + key_len + 2 + val_len > wire->buf_len)
                    break;
            } else {
                val_len = 0;
            }

            /* ok - we have a new key/value pair to add to the box.  First
             * expand the box to fit -- use +2 to have room for new key and
             * terminating NULL */
            if (wire->box_len + 2 > wire->box_size) {
                int i;

                wire->box_size *= 2;
                wire->box = realloc(wire->box, wire->box_size * sizeof(remsh_box));
            }

            /* then add the key/value pair */
            if (key_len > 0) {
                offset = wire->buf_start + wire->box_bytes;
                wire->box[wire->box_len].key_len = key_len;
                offset += 2;
                wire->box[wire->box_len].key = (char *)&wire->buf[offset];
                offset += key_len;
                wire->box[wire->box_len].val_len = val_len;
                offset += 2;
                wire->box[wire->box_len].val = (char *)&wire->buf[offset];
                offset += val_len;

                wire->box_len++;
            } else {
                offset = wire->buf_start + wire->box_bytes + 2;
                wire->box[wire->box_len].key = NULL;
                wire->box[wire->box_len].key_len = 0;
                wire->box[wire->box_len].val = NULL;
                wire->box[wire->box_len].val_len = 0;
            }

            /* and reset the box_bytes to cover the area just parsed */
            wire->box_bytes = offset - wire->buf_start;

            /* if key_len is 0, we've got a box */
            if (key_len == 0) {
                /* terminate the box with NULLs */
                wire->box[wire->box_len].key = NULL;
                wire->box[wire->box_len].key_len = 0;
                wire->box[wire->box_len].val = NULL;
                wire->box[wire->box_len].val_len = 0;
                if (box)
                    *box = wire->box;
                return 0;
            }
        }

        /* a 'break' above means we don't have enough data, so read some more, first
         * freeing up some buffer space */

        box_invalid = 0;
        if (wire->buf_start != 0 && wire->buf_len != 0) {
            /* move the contents of the buffer back to the start */
            memmove(wire->buf, wire->buf+wire->buf_start, wire->buf_len);
            wire->buf_start = 0;

            box_invalid = 1;
        }
        if (wire->buf_len == wire->buf_size) {
            /* reallocate a bigger buffer */
            wire->buf_size *= 2;
            wire->buf = realloc(wire->buf, wire->buf_size);

            box_invalid = 1;
        }

        /* if we've invalidated the box by moving data, zero it out.  We'll
         * re-scan it in a few minutes. */
        if (box_invalid) {
            wire->box_len = 0;
            wire->box_bytes = 0;
        }

        bytes = remsh_xport_read(wire->xport,
                wire->buf + wire->buf_start + wire->buf_len,
                wire->buf_size - wire->buf_start - wire->buf_len);
        if (bytes < 0) {
            return -1; /* xport error */
        } else if (bytes == 0) {
            if (wire->buf_len) {
                return -1; /* leftover bytes on EOF */
            } else {
                if (box)
                    *box = NULL;
                return 0;
            }
        } else {
            wire->buf_len += bytes;
        }
    }
}

void remsh_wire_box_extract(remsh_box *box, remsh_box *extract)
{
    remsh_box *ex, *b;

    for (ex = extract; ex->key; ex++) {
        ex->val = NULL;
        ex->val_len = 0;

        if (!ex->key_len) {
            int key_len = strlen(ex->key);
            if (key_len < 0 || key_len > 255)
                continue; /* an invalid key won't be found.. */
            ex->key_len = key_len;
        }

        for (b = box; b->key; b++) {
            if (ex->key_len != b->key_len)
                continue;
            if (memcmp(ex->key, b->key, ex->key_len) != 0)
                continue;

            ex->val = b->val;
            ex->val_len = b->val_len;
            break;
        }
    }
}

char *
remsh_wire_box_repr(remsh_box *box)
{
    char *rv, *p;
    remsh_box *b;
    size_t len;

    if (!box)
        return strdup("(null)");

    /* calculate the length of the resulting string */
    len = 4; /* '{ ' .. '}\0' */
    for (b = box; b->key; b++) {
        if (!b->key_len)
            b->key_len = strlen(b->key);
        len += 9 + b->key_len + b->val_len; /* '"' .. '" : "' .. '", ' */
    }
    p = rv = malloc(len);

    /* build the string */
    *(p++) = '{';
    *(p++) = ' ';
    for (b = box; b->key; b++) {
        *(p++) = '"';
        memcpy(p, b->key, b->key_len);
        p += b->key_len;
        *(p++) = '"';
        *(p++) = ' ';
        *(p++) = ':';
        *(p++) = ' ';
        *(p++) = '"';
       memcpy(p, b->val, b->val_len);
        p += b->val_len;
        *(p++) = '"';
        *(p++) = ',';
        *(p++) = ' ';
    }
    *(p++) = '}';
    *(p++) = '\0';

    return rv;
}

remsh_wire *remsh_wire_new(remsh_xport *xport)
{
    remsh_wire *wire = calloc(1, sizeof(remsh_wire));
    if (!wire)
        return NULL;

    wire->xport = xport;

    wire->buf = malloc(32768);
    wire->buf_size = 32768;

    wire->box = calloc(32, sizeof(remsh_box));
    wire->box_size = 32;
}

int remsh_wire_close(remsh_wire *wire)
{
    if (remsh_xport_close(wire->xport) < 0)
        return -1;

    free(wire->buf);
    free(wire);

    return 0;
}
