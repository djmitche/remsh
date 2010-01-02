/* This file is part of remsh
 * Copyright 2009, 2010, 2010 Dustin J. Mitchell
 * See COPYING for license information
 */

#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <assert.h>
#include "remsh.h"
#include "testutils.h"

int main(void)
{
    int p[2];
    remsh_xport *wxp, *rxp;
    remsh_wire *wwire, *rwire;
    char *str;

    testutil_init();

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
        remsh_box box[] = {
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
        remsh_box badbox[] = {
            { 0, "", 4, "nono", },
            { 0, NULL, 0, NULL, },
        };

        test_call_ok(remsh_wire_send_box(wwire, box), NULL,
                "send box 1");
        test_is_int(remsh_xport_read(rxp, buf, sizeof(buf)), sizeof(expected)-1,
                "read correct size");
        test_is_int(memcmp(buf, expected, sizeof(expected)-1), 0,
                "buffer data matches (binary)");
        test_is_int(remsh_wire_send_box(wwire, badbox), -1,
                "send bad box");
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
        remsh_box get1[] = {
            { 4, "name", 0, NULL, },
            { 0, NULL, 0, NULL, },
        };
        remsh_box get2[] = {
            { 13, "hloxwfxotvcaq", 0, NULL, },
            { 0, "x", 0, NULL, },
            { 0, NULL, 0, NULL, },
        };
        remsh_box get3[] = {
            { 0, "y", 0, NULL, },
            { 0, "x", 0, NULL, },
            { 0, "z", 0, (char *)13, },
            { 0, NULL, 0, NULL, },
        };
        remsh_box *res;

        test_call_ok(remsh_xport_write(wxp, data, sizeof(data)-1), wxp->errmsg,
                "write data");
        test_call_ok(remsh_wire_read_box(rwire, &res), NULL,
                "read first box");
        test_is_int(box_len(res), 3,
                "first box length is correct");

        test_is_str((str = remsh_wire_box_repr(res)),
                "{ \"name\" : \"lark\", \"x\" : \"\", \"hloxwfxotvcaq\" : \"z\", }",
                "box repr is correct");
        free(str);

        remsh_wire_box_extract(res, get1);
        test_is_str(get1[0].val, "lark",
                "extracted correct value");

        remsh_wire_box_extract(res, get2);
        test_is_str(get2[0].val, "z",
                "extracted correct value");
        test_is_int(get2[1].val_len, 0,
                "x is empty");
        test_is_not_null(get2[1].val,
                "x is not NULL");

        test_call_ok(remsh_wire_read_box(rwire, &res), NULL,
                "read second box");
        test_is_int(box_len(res), 2,
                "second box has two elements");

        remsh_wire_box_extract(res, get3);
        test_is_str(get3[0].val, "x",
                "short value is correct");
        test_is_int(get3[1].val_len, 0x100,
                "long value len is correct");
        test_is_null(get3[2].val,
                "nonexistent key returned NULL");
    }

    /* test writing */
    {
        remsh_box box1[] = {
            { 0, "meth", 4, "edit", },
            { 0, "version", 1, "2", },
            { 6, "object", 5, "fe\091", },
            { 0, NULL, 0, NULL, },
        };
        remsh_box box2[] = {
            { 0, "meth", 4, "save", },
            { 0, "version", 1, "3", },
            { 4, "data", 0, "" },
            { 6, "object", 5, "fe\091", },
            { 0, NULL, 0, NULL, },
        };

        char data[] =
            "\x00\x04""meth"          "\x00\x04""edit"
            "\x00\x07""version"       "\x00\x01""2"
            "\x00\x06""object"        "\x00\x05""fe\091"
            "\x00\x00" /* 41 bytes */

            "\x00\x04""meth"          "\x00\x04""save"
            "\x00\x07""version"       "\x00\x01""3"
            "\x00\x04""data"          "\x00\x00"
            "\x00\x06""object"        "\x00\x05""fe\091"
            "\x00\x00"; /* 49 bytes */
        char buf[1024];

        test_call_ok(remsh_wire_send_box(wwire, box1), NULL,
                "send first box");
        test_call_ok(remsh_wire_send_box(wwire, box2), NULL,
                "send second box");
        test_is_int(remsh_xport_read(rxp, buf, sizeof(buf)), 90,
                "two boxes take up 90 bytes");
        test_is_int(memcmp(buf, data, 90), 0,
                "binary data matches");
    }

    testutil_cleanup();
    return 0;
}
