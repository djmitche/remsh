# This file is part of Remsh.
#
# Remsh is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Remsh is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Remsh.  If not, see <http://www.gnu.org/licenses/>.

"""
This is a very simple, un-twisted implementation of the AMP wire protocol.  See
http://twistedmatrix.com/documents/8.1.0/api/twisted.protocols.amp.html.

Note that this implements *only* the wire protocol.  AMP's purpose-specific
keys (_ask, _answer, etc.) are not supported, and this does not implement a
request/response protocol.

Note that this implementation is entirely synchoronous -- the upper-level
protocol must *always* know whether it expects an incoming message or not, or
it will deadlock.
"""

# Note (outside the docstring) that this is ridiculously inefficient, doing no
# read buffering.  It's a prototype.  Enjoy.

import struct

class Error(Exception):
    """Protocol error"""

class Connection(object):
    """
    A wrapper around a socket to send and receive AMP-formatted "boxes".

    A box is represented as a Python dictionary with string keys and values.
    Key length must be less than 256 bytes, while values must be less than
    65536 (2**16) bytes.
    """

    def __init__(self, socket):
        self.socket = socket

    def _full_read(self, bytes):
        """Read exactly len bytes and return them.  Returns None on EOF, but raises
        EOFError if any bytes are read before EOF."""
        buf = ''
        remaining = bytes
        while len(buf) < bytes:
            d = self.socket.recv(bytes)
            if not d:
                if buf: raise EOFError("EOF in the middle of a read")
                return None
            remaining -= len(d)
            buf += d
        return buf

    def _full_write(self, val):
        """Write all of val to self.socket."""
        while val:
            written = self.socket.send(val)
            val = val[written:]

    def read_box(self):
        """
        Read a whole box from the socket and return it, or return None on EOF.
        If the EOF occurs in the middle of a box, raises EOFError.  On protocol
        errors (duplicate keys, etc.), raises an Error.
        """
        box = {}

        while 1:
            klen = self._full_read(2)
            if not klen:
                if not box: return
                raise EOFError("EOF in the middle of a box")
            klen = struct.unpack("!H", klen)[0]
            if klen == 0: break
            if klen > 255: raise Error("key length %d is > 255" % klen)

            key = self._full_read(klen)
            if not key: raise EOFError("EOF in the middle of a box")

            if key in box: raise Error("Duplicate key in box");

            vlen = self._full_read(2)
            if not vlen: raise EOFError("EOF in the middle of a box")
            vlen = struct.unpack("!H", vlen)[0]

            value = self._full_read(vlen)
            if not value: raise EOFError("EOF in the middle of a box")

            box[key] = value

        return box

    def send_box(self, box):
        """
        Send the given box.  As a convenience, values are stringified if
        necessary.  If the box is invalid (a key or value is too large), raises
        Error.
        """
        for k,v in box.iteritems():
            k = str(k)
            if len(k) > 255: raise Error("key length must be <= 255")
            self._full_write(struct.pack("!H", len(k)) +  k)
            v = str(v)
            if len(v) > 65535: raise Error("value length must be <= 65535")
            self._full_write(struct.pack("!H", len(v)) +  str(v))
        self._full_write(struct.pack("!H", 0))
