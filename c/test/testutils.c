/* This file is part of remsh
 * Copyright 2009 Dustin J. Mitchell
 * See COPYING for license information
 */

#include <stdio.h>
#include <assert.h>
#include "remsh.h"
#include "testutils.h"

#include "remsh.h"

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

