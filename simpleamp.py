# Implement a simple streamable protocol, using AMP's wire protocol but not the
# _command, _ask, _error, etc.

# Note that this is entirely synchoronous -- the upper-level protocol must
# *always* know whether it expects an incoming message or not, or it will
# deadlock.

# Note that this is ridiculously inefficient, doing no read buffering.  It's a
# prototype.

import struct

class Error(Exception):
    """Protocol error"""

class Connection(object):
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
        """Read a whole box from the socket and return it, or return None on
        EOF.  If the EOF occurs in the middle of a box, raises EOFError.  A box
        is represented as a regular Python dictionary."""

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

        print "incoming box:", box
        return box

    def send_box(self, box):
        """Send the given box."""
        for k,v in box.iteritems():
            k = str(k)
            if len(k) > 255: raise Error("key length must be <= 255")
            self._full_write(struct.pack("!H", len(k)) +  k)
            v = str(v)
            if len(v) > 65535: raise Error("value length must be <= 65535")
            self._full_write(struct.pack("!H", len(v)) +  v)
        self._full_write(struct.pack("!H", 0))
