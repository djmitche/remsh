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
see doc/developer/amp.rst
"""

import struct
import types
import select
import threading
import Queue

class Error(Exception):
    """Protocol error"""

class SimpleWire(object):
    def __init__(self, socket):
        self.socket = socket
        self.read_buf = ''

    ##
    # Public interface

    def send_box(self, box):
        """
        """
        bytes = self._box_to_bytes(box)
        self.socket.sendall(bytes)

    def read_box(self):
        """
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

    def stop(self):
        """
        Stop using the socket.
        """
        pass # no need to do anything in the SimpleWire

    ##
    # Utility functions

    def _box_to_bytes(self, box):
        """
        Turn a box into a byte sequence.  Raises an Error for an invalid packet.
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
        Turn a sequence of bytes into a tuple (box, remaining_bytes), where box
        is None if a full box's worth of data is not available.  Raises an
        Error for an invalid packet.
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

class ResilientWire(SimpleWire):
    # TODO: how should this signal a socket failure for re-establishment?

    def __init__(self, socket):
        SimpleWire.__init__(self, socket)
        self.incoming_boxes = Queue.Queue()
        self.done = False

        self.thread = threading.Thread(target=self._read_loop)
        self.thread.setDaemon(1)
        self.thread.start()

        self.write_lock = threading.Lock()

    ##
    # Public methods

    def send_box(self, box):
	# for sending, this class simply locks the socket for writing
	# and sends the box using the parent class's method
        # TODO: does this unnecessarily block the thread?
        self.write_lock.acquire()
        try:
            SimpleWire.send_box(self, box)
            # TODO: error handling
        finally:
            self.write_lock.release()

    def read_box(self):
        box = self.incoming_boxes.get()
        if box is None: # semaphore for EOF; put it back for the next read
            self.incoming_boxes.put(None)
        return box

    def stop(self):
        # note: this may block for a little while
        self.done = True
        self.thread.join()

    ##
    # Internal implementation

    def _read_loop(self):
        self.socket.setblocking(0)

        while not self.done:
            rd = [ self.socket ]
            wr = []
            ex = [ self.socket ]
            try: rd, wr, ex = select.select(rd, wr, ex, 0.5) # timeout is for stop()
            except: print rd, wr, ex; raise

            if rd or ex:
                if not self.handle_read(): break

    def handle_read(self):
        data = self.socket.recv(1024*16)
        if not data:
            self.incoming_boxes.put(None) # EOF indication
            return False

        self.read_buf += data
        while 1:
            box, self.read_buf = self._bytes_to_box(self.read_buf)
            if not box: break
            self.incoming_boxes.put(box)
        return True
