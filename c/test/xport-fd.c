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

int main(void)
{
    int p[2];
    remsh_xport *wxp, *rxp;
    char buf[256];

    if (pipe(p) < 0) {
        perror("pipe");
        return 1;
    }

    rxp = remsh_fd_xport_new(p[0]);
    wxp = remsh_fd_xport_new(p[1]);

    /* note that this assumes sufficient buffer space .. 4096 bytes seems a
     * minimal pipe buffer, so we're nowhere near it */

    /* simple read and write */
    assert(0 == remsh_xport_write(wxp, "WORDS", 5));
    assert(5 == remsh_xport_read(rxp, buf, 5));
    assert(0 == strncmp(buf, "WORDS", 5));

    /* writes should get batched up */
    assert(0 == remsh_xport_write(wxp, "BOOKKEEPER", 10));
    assert(0 == remsh_xport_write(wxp, "BOOKKEEPER", 10));
    assert(20 == remsh_xport_read(rxp, buf, sizeof(buf)));
    assert(0 == strncmp(buf, "BOOKKEEPERBOOKKEEPER", 20));

    /* and reads can be misaligned with writes */
    assert(0 == remsh_xport_write(wxp, "0mS(DF09sdf0m9sdf8msd09KSDF9821nSD)MF09sdf", 42));
    assert(0 == remsh_xport_write(wxp, "asdfk0-9j2198nSD(*Fn09sdmf0", 27));
    assert(50 == remsh_xport_read(rxp, buf, 50));
    assert(19 == remsh_xport_read(rxp, buf, sizeof(buf)));

    /* close the write end, and make sure we read an EOF after the remainder of the bytestream */
    assert(0 == remsh_xport_write(wxp, "abcd", 4));
    remsh_xport_close(wxp);
    assert(4 == remsh_xport_read(rxp, buf, sizeof(buf)));
    assert(0 == remsh_xport_read(rxp, buf, sizeof(buf)));
    assert(0 == remsh_xport_read(rxp, buf, sizeof(buf))); /* EOF is "sticky" */

    return 0;
}
