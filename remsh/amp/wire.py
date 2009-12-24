# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information
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
            rd = [self.socket]
            wr = []
            ex = [self.socket]
            try:
                # timeout is for stop()
                rd, wr, ex = select.select(rd, wr, ex, 0.5)
            except:
                print rd, wr, ex
                raise

            if (rd or ex) and not self.handle_read():
                break

    def handle_read(self):
        data = self.socket.recv(1024*16)
        if not data:
            self.incoming_boxes.put(None) # EOF indication
            return False

        self.read_buf += data
        while 1:
            box, self.read_buf = self._bytes_to_box(self.read_buf)
            if not box:
                break
            self.incoming_boxes.put(box)
        return True
