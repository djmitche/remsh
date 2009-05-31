# This file is part of remsh.
#
# remsh is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# remsh is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with remsh.  If not, see <http://www.gnu.org/licenses/>.

"""
This is a very simple, asyncore-based implementation of the AMP wire
protocol.  See
http://twistedmatrix.com/documents/8.1.0/api/twisted.protocols.amp.html.
"""

import struct
import types
import select
import threading

class Error(Exception):
    """Protocol error"""

class SimpleWire(object):
    """

    An implementation of the AMP wire protocol, presenting a synchronous
    interface to the main thread.  This interface assumes that the
    higher-level protocol is strictly turn-based, so that each side
    always knows which side will send the next box.

    This is the simpler implementation of this protocol, operating
    entirely synchronously.

    """

    def __init__(self, socket):
        self.socket = socket
        self.read_buf = ''

    ##
    # Public interface

    def send_box(self, box):
        """
	Send the given box, returning once it is completley transmitted
	(but not necessarily received by the remote end).

        Raises Error for protocol errors or socket.error for network errors.
        """
        bytes = self._box_to_bytes(box)
        self.socket.sendall(bytes)

    def read_box(self):
        """
        Read a box from the remote system, blocking until one is received

	Raises Error for protocol errors or socket.error for network
	errors.  Returns None on a normal EOF, or EOFError on an EOF in
	the middle of a box.
        """
        # avoid reading anything from the socket if not necessary
        if self.read_buf:
            box, self.read_buf = self._bytes_to_box(self.read_buf)
            if box: return box

        while 1:
            newd = self.socket.recv(4096)
            if not newd:
                if self.read_buf != '': raise EOFError
                return
            box, self.read_buf = self._bytes_to_box(self.read_buf + newd)
            if box: return box

    ##
    # Utility functions

    def _box_to_bytes(self, box):
        """

        Turn a box into a byte sequence.

	Raises an Error for an invalid packet.

        """
        bytes = []
        for k, v in box.iteritems():
            if type(k) != types.StringType: k = str(k)
            if len(k) > 255: raise Error("key length must be < 256")
            if len(k) < 1: raise Error("key length must be nonzero")
            bytes.append(struct.pack("!H", len(k)) +  k)
            if type(v) != types.StringType: v = str(v)
            if len(v) > 65535: raise Error("value length must be <= 65535")
            bytes.append(struct.pack("!H", len(v)) +  str(v))
        bytes.append('\x00\x00')
        return ''.join(bytes)

    def _bytes_to_box(self, bytes):
        """

        Turn a sequence of bytes into a tuple (box, remaining_bytes), where
        box is None if a full box's worth of data is not available.

	Raises an Error for an invalid packet.

        """

        # see if we have a full box
        pos = 0
        nbytes = len(bytes)
        while 1:
            if pos + 2 > nbytes: return (None, bytes) # not enough bytes
            klen = struct.unpack("!H", bytes[pos:pos+2])[0]
            if klen >= 256: raise Error("invalid key length 0x%04x" % klen)
            if klen == 0: break # found a full box
            if pos + 2 + klen + 2 > nbytes: return (None, bytes)
            vlen = struct.unpack("!H", bytes[pos+2+klen:pos+2+klen+2])[0]
            if pos + 2 + klen + 2 + vlen > nbytes: return (None, bytes)
            pos += 2 + klen + 2 + vlen

        # at this point, bytes[0:pos+2] is a full box, so convert it to
        # a dictionary and return it
        remaining = bytes[pos+2:]
        pos = 0
        box = {}
        while 1:
            klen = struct.unpack("!H", bytes[pos:pos+2])[0]
            key = bytes[pos+2:pos+2+klen]
            if klen == 0: break
            vlen = struct.unpack("!H", bytes[pos+2+klen:pos+2+klen+2])[0]
            val = bytes[pos+2+klen+2:pos+2+klen+2+vlen]
            if key in box: raise Error("duplicate key %r" % key)
            box[key] = val
            pos += 2 + klen + 2 + vlen

        return (box, remaining)

class Simple(object):
    """

    An AMP box is represented as a Python dictionary with string keys
    and values.  Key length must be less than 256 bytes, while values
    must be less than 65536 (2**16) bytes.

    """

    ##
    # Public methods

    def _loop(self):
        self.socket.setblocking(0)

    def handle_read(self):
        try:
            data = self.socket.recv(1024*16)
        except socket.error:
            self.handle_error()
            return
        self.buffer = self.buffer + data

        self._process_buffer()

    def _process_buffer(self):
        """
        Extract any key/value pairs in self.buffer into self.incoming_box, calling
        handle_box with any completed boxes.
        """
        if self.incoming_box is None:
            self.incoming_box = {}
        buf = self.buffer

        try:
            while 1:
                if len(buf) < 2: break # not enough data yet

                klen = struct.unpack("!H", buf[:2])[0]
                if klen == 0:
                    buf = buf[2:]
                    # push out a box
                    try:
                        self.handle_box(self.incoming_box)
                    finally:
                        self.incoming_box = {}
                    continue

                if klen > 255: raise Error("key length %d is > 255" % klen)
                if len(buf) < 2 + klen + 2: break # not enough data yet
                voffset = 2 + klen
                vlen = struct.unpack("!H", buf[voffset:voffset+2])[0]

                if len(buf) < 2 + klen + 2 + vlen: break # not enough data yet

                # we have a full key/value pair, so add it to self.incoming_box
                key, value, buf = buf[2:2+klen], buf[voffset+2:voffset+2+vlen], buf[voffset+2+vlen:]
                if key in self.incoming_box:
                    raise Error("duplicate key %r in incoming box" % key)
                self.incoming_box[key] = value
        finally:
            self.buffer = buf

    def handle_box(self, box):
        """
        Override this in subclasses to handle incoming boxes.
        """

    def send_box(self, box):
        """
	Send the given box.  As a convenience, values are stringified if
	necessary.  If the box is invalid (a key or value is too large),
	raises Error immediately.  Other socket-related exceptions may
	also occur.
        """
        for k,v in box.iteritems():
            k = str(k)
            if len(k) > 255: raise Error("key length must be <= 255")
            if len(k) < 1: raise Error("key length must be nonzero")
            self.send(struct.pack("!H", len(k)) +  k)
            v = str(v)
            if len(v) > 65535: raise Error("value length must be <= 65535")
            self.send(struct.pack("!H", len(v)) +  str(v))
        self.send(struct.pack("!H", 0))
