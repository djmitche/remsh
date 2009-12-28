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
    remsh_wire *wwire, *rwire;

    if (pipe(p) < 0) {
        perror("pipe");
        return 1;
    }

    rxp = remsh_fd_xport_new(p[0]);
    rwire = remsh_wire_new(rxp);

    wxp = remsh_fd_xport_new(p[1]);
    wwire = remsh_wire_new(wxp);

    /* test writing */
    {
        char buf[256];
        remsh_box_kv box[] = {
            { 4, "name", 4, "lark", },
            { 1, "x", 0, "", },
            { 0, "hloxwfxotvcaq", 1, "z", },
            { 0, NULL, 0, NULL, },
        };
        char expected[] =
            "\x00\x04name"          "\x00\x04lark"
            "\x00\x01x"             "\x00\x00"
            "\x00\x0dhloxwfxotvcaq" "\x00\x01z"
            "\x00\x00";
        remsh_box_kv badbox[] = {
            { 0, "", 4, "nono", },
            { 0, NULL, 0, NULL, },
        };

        assert(0 == remsh_wire_send_box(wwire, box));
        assert(sizeof(expected)-1 == remsh_xport_read(rxp, buf, sizeof(buf)));
        assert(0 == memcmp(buf, expected, sizeof(expected)-1));
        assert(-1 == remsh_wire_send_box(wwire, badbox));
    }

    /* test reading */
    {
        char data[] =
            "\x00\x04name"          "\x00\x04lark"
            "\x00\x01x"             "\x00\x00"
            "\x00\x0dhloxwfxotvcaq" "\x00\x01z"
            "\x00\x00"

            "\x00\x01x"             "\x01\x00"
             "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
             "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
             "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
             "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
            "\x00\x01y"             "\x00\x01x"
            "\x00\x00";

        int nkeys;
        remsh_box_kv get1[] = {
            { 4, "name", 0, NULL, },
            { 0, NULL, 0, NULL, },
        };
        remsh_box_kv get2[] = {
            { 13, "hloxwfxotvcaq", 0, NULL, },
            { 0, "x", 0, NULL, },
            { 0, NULL, 0, NULL, },
        };

        assert(0 == remsh_xport_write(wxp, data, sizeof(data)-1));
        assert(0 == remsh_wire_read_box(rwire, &nkeys));
        assert(3 == nkeys);

        remsh_wire_get_box_data(rwire, get1);
        assert(4 == get1[0].val_len);
        assert(0 == memcmp("lark", get1[0].val, 4));
        assert('\0' == get1[0].val[4]); /* check zero termination */

        remsh_wire_get_box_data(rwire, get2);
        assert(1 == get2[0].val_len);
        assert(0 == memcmp("z", get2[0].val, 1));
        assert(0 == get2[1].val_len);
        assert(NULL != get2[1].val);

        /* more .. */
    }

    return 0;
}
