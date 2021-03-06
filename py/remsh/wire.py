# This file is part of remsh
# Copyright 2009, 2010 Dustin J. Mitchell
# See COPYING for license information
# -*- test-case-name: test.test_wire -*-

import os
import types
import struct


class Error(Exception):
    "Wire-layer error"


class Wire(object):

    def __init__(self, xport):
        self.xport = xport
        self.read_buf = ''
        self.debug = 0

    def send_box(self, box):
        if self.debug:
            print ">> ", box
        bytes = self._box_to_bytes(box)
        self.xport.write(bytes)

    def read_box(self):
        # avoid reading anything from the socket if not necessary
        if self.read_buf:
            box, self.read_buf = self._bytes_to_box(self.read_buf)
            if box:
                return box

        while 1:
            newd = self.xport.read()
            if not newd:
                if self.read_buf != '':
                    raise EOFError
                return None
            box, self.read_buf = self._bytes_to_box(self.read_buf + newd)
            if box is not None:
                if self.debug:
                    print "<< ", box
                return box

    def close(self):
        self.xport.close()

    ##
    # Utility functions

    def _box_to_bytes(self, box):
        """
        Turn a box into a byte sequence.  Raises an Error for an
        invalid packet.
        """
        bytes = []
        for k, v in box.iteritems():
            if type(k) != types.StringType:
                k = str(k)
            if len(k) > 255:
                raise Error("key length must be < 256")
            if len(k) < 1:
                raise Error("key length must be nonzero")
            bytes.append(struct.pack("!H", len(k)) + k)
            if type(v) != types.StringType:
                v = str(v)
            if len(v) > 65535:
                raise Error("value length must be <= 65535")
            bytes.append(struct.pack("!H", len(v)) + str(v))
        bytes.append('\x00\x00')
        return ''.join(bytes)

    def _bytes_to_box(self, bytes):
        """
        Turn a sequence of bytes into a tuple (box, remaining_bytes), where box
        is None if a full box's worth of data is not available.  Raises an
        Error for an invalid packet.
        """

        # see if we have a full box
        pos = 0
        nbytes = len(bytes)
        while 1:
            if pos + 2 > nbytes:
                return (None, bytes) # not enough bytes
            klen = struct.unpack("!H", bytes[pos:pos + 2])[0]
            if klen >= 256:
                raise Error("invalid key length 0x%04x" % klen)
            if klen == 0:
                break # found a full box
            if pos + 2 + klen + 2 > nbytes:
                return (None, bytes)
            vlen = struct.unpack("!H",
                bytes[pos + 2 + klen:pos + 2 + klen + 2])[0]
            if pos + 2 + klen + 2 + vlen > nbytes:
                return (None, bytes)
            pos += 2 + klen + 2 + vlen

        # at this point, bytes[0:pos+2] is a full box, so convert it to
        # a dictionary and return it
        remaining = bytes[pos + 2:]
        pos = 0
        box = {}
        while 1:
            klen = struct.unpack("!H", bytes[pos:pos + 2])[0]
            key = bytes[pos + 2:pos + 2 + klen]
            if klen == 0:
                break

            vlen = struct.unpack("!H",
                bytes[pos + 2 + klen:pos + 2 + klen + 2])[0]

            val = bytes[pos + 2 + klen + 2:pos + 2 + klen + 2 + vlen]
            if key in box:
                raise Error("duplicate key %r" % key)
            box[key] = val
            pos += 2 + klen + 2 + vlen

        return (box, remaining)
