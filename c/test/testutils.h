/* This file is part of remsh
 * Copyright 2009 Dustin J. Mitchell
 * See COPYING for license information
 */

#ifndef TESTUTILS_H
#define TESTUTILS_H

#include "remsh.h"

/* return the number of keys in the given box, or -1 if the box is empty */
int box_len(remsh_box *box);

/* pretty-print the given box to stdout, with the given prefix */
void box_pprint(char *prefix, remsh_box *box);

#endif
