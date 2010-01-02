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
#include "testutils.h"

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
    test_call_ok(remsh_xport_write(wxp, "WORDS", 5), wxp->errmsg,
            "write is OK");
    test_is_int(remsh_xport_read(rxp, buf, 5), 5,
            "and read returns all bytes");
    buf[5] = '\0';
    test_is_str(buf, "WORDS",
            "and the correct bytes, too");

    /* writes should get batched up */
    test_call_ok(remsh_xport_write(wxp, "BOOKKEEPER", 10), wxp->errmsg,
            "batched write 1 OK");
    test_call_ok(remsh_xport_write(wxp, "BOOKKEEPER", 10), wxp->errmsg,
            "batched write 1 OK");
    test_is_int(remsh_xport_read(rxp, buf, sizeof(buf)), 20,
            "writes are batched into 20 bytes");
    buf[20] = '\0';
    test_is_str(buf, "BOOKKEEPERBOOKKEEPER",
            "and correct bytes are present");

    /* and reads can be misaligned with writes */
    test_call_ok(remsh_xport_write(wxp, "0mS(DF09sdf0m9sdf8msd09KSDF9821nSD)MF09sdf", 42),
            wxp->errmsg,
            "write 1");
    test_call_ok(remsh_xport_write(wxp, "asdfk0-9j2198nSD(*Fn09sdmf0", 27), wxp->errmsg,
            "write 2");
    test_is_int(remsh_xport_read(rxp, buf, 50), 50,
            "first read returns as much as requested");
    test_is_int(remsh_xport_read(rxp, buf, sizeof(buf)), 19,
            "second read returns remainder");

    /* close the write end, and make sure we read an EOF after the remainder of the bytestream */
    test_call_ok(remsh_xport_write(wxp, "abcd", 4), wxp->errmsg,
            "one last write");
    test_call_ok(remsh_xport_close(wxp), wxp->errmsg,
            "close write xport");
    test_is_int(remsh_xport_read(rxp, buf, sizeof(buf)), 4,
            "read those last bytes");
    test_is_int(remsh_xport_read(rxp, buf, sizeof(buf)), 0,
            "returns 0 on EOF");
    test_is_int(remsh_xport_read(rxp, buf, sizeof(buf)), 0,
            "still returns 0 on EOF");

    return 0;
}
