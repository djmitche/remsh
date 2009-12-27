/* This file is part of remsh
 * Copyright 2009 Dustin J. Mitchell
 * See COPYING for license information
 */

#ifndef UTIL_H
#define UTIL_H

#include "remsh.h"

/* set the error message for a remsh_xport; this takes
 * ownership of the given string */
void remsh_set_errmsg(remsh_xport *self, char *msg);

#endif /* UTIL_H */
