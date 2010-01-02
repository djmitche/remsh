/* This file is part of remsh
 * Copyright 2009, 2010, 2010 Dustin J. Mitchell
 * See COPYING for license information
 */

#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <limits.h>
#include <errno.h>
#include "remsh.h"
#include "util.h"

/* "base" directory for a cwd-less set_cwd */
static char *base_dir = NULL;

/*
 * Utilities
 */

static int
send_errbox(remsh_wire *wire, char *errtag, char *error)
{
    remsh_box errbox[] = {
        { 6, "errtag", strlen(errtag), errtag },
        { 5, "error", strlen(error), error },
        { 0, NULL, 0, NULL },
    };

    return remsh_wire_send_box(wire, errbox);
}

/*
 * Operations
 */

typedef int (* op_fn)(remsh_box *rq_box, remsh_wire *rwire, remsh_wire *wwire);

struct op_version {
    int version;
    op_fn fn;
};

struct op_meth {
    char *name;
    struct op_version *versions;
};

static int
set_cwd_1(remsh_box *rq_box, remsh_wire *rwire, remsh_wire *wwire)
{
    char *cwd;
    char new_wd[PATH_MAX];

    remsh_box args[] = {
        { 0, "cwd", 0, NULL },
        { 0, NULL, 0, NULL },
    };
    remsh_box reply[] = {
        { 0, "cwd", 0, NULL },
        { 0, NULL, 0, NULL },
    };

    remsh_wire_box_extract(rq_box, args);
    cwd = args[0].val;

    if (!cwd)
        cwd = base_dir;

    if (*cwd && chdir(cwd) < 0) {
        if (errno == ENOENT)
            return send_errbox(wwire, "notfound", "new directory not found");
        else
            return send_errbox(wwire, "unexpected", strerror(errno));
    }

    if (getcwd(new_wd, PATH_MAX) < 0)
        return send_errbox(wwire, "unexpected", strerror(errno));

    reply[0].val = new_wd;
    reply[0].val_len = strlen(new_wd);
    return remsh_wire_send_box(wwire, reply);
}

static struct op_version set_cwd_versions[] = {
    { 1, set_cwd_1 },
    { 0, NULL },
};

static struct op_meth op_meths[] = {
    { "set_cwd", set_cwd_versions },
    { NULL, NULL },
};

/*
 * Dispatcher
 */

void
remsh_op_init(void)
{
    char path[PATH_MAX];

    if (getcwd(path, PATH_MAX) < 0)
        base_dir = strdup("/");
    else
        base_dir = strdup(path);
}

int
remsh_op_perform(remsh_wire *rwire, remsh_wire *wwire, int *eof)
{
    remsh_box *box;
    remsh_box meth_info[] = {
        { 0, "meth", 0, NULL },
        { 0, "version", 0, NULL },
        { 0, NULL, 0, NULL },
    };
    char *meth;
    int version = -1;
    char *tmp;
    struct op_meth *m;
    struct op_version *v;
    int nkeys;

    *eof = 0;

    if (remsh_wire_read_box(rwire, &box) < 0)
        return -1;

    if (!box) {
        *eof = 1;
        return 0;
    }

    remsh_wire_box_extract(box, meth_info);
    meth = meth_info[0].val;
    if (meth_info[1].val && meth_info[1].val_len) {
        version = strtol(meth_info[1].val, &tmp, 10);
        if (tmp != meth_info[1].val + meth_info[1].val_len)
            version = -1;
    }

    if (!meth || version == -1) {
        return send_errbox(wwire, "invalid", "invalid request");
    }

    for (m = op_meths; m->name; m++) {
        if (0 == strcmp(m->name, meth)) {
            int found_higher = 0;

            for (v = m->versions; v->fn; v++) {
                if (v->version == version)
                    return v->fn(box, rwire, wwire);
                if (v->version > version)
                    found_higher = 1;
            }

            if (found_higher)
                return send_errbox(wwire, "version-unsupported",
                                   "requested version not supported");
            else
                return send_errbox(wwire, "version-too-new",
                                   "requested version is newer than highest supported");
        }
    }

    return send_errbox(wwire, "invalid-meth", "unknown method");
}

int
remsh_op_loop(remsh_wire *rwire, remsh_wire *wwire)
{
    int eof = 0;

    while (!eof) {
        if (remsh_op_perform(rwire, wwire, &eof) < 0)
            return -1;
    }

    return 0;
}
