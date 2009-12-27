/* This file is part of remsh
 * Copyright 2009 Dustin J. Mitchell
 * See COPYING for license information
 */

#include <stdlib.h>
#include <string.h>
#include "remsh.h"
#include "util.h"

void
remsh_set_errmsg(remsh_xport *self, char *msg)
{
    if (self->errmsg)
        free(self->errmsg);
    self->errmsg = msg;
}
