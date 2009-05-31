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

import unittest
import threading
import socket
import os
import time

from remsh.amp import wire

NAGLE_SLEEP = 0.05

class TestWireReadingMixin(object):
    # test reading packets from ampwire; the mixin uses self.wire_class as the
    # class to test

    def read_with_wire(self, writes):
        """Make a socket to which each string in WRITES is written, separated by a
        pause long enough to avoid invoking Nagle's algorithm."""
        wire_socket, thread_sock = socket.socketpair()

        def thd():
            for wr in writes:
                thread_sock.sendall(wr)
                time.sleep(NAGLE_SLEEP)
            thread_sock.close()
        self.thread = threading.Thread(target=thd)
        self.thread.setDaemon(1)
        self.thread.start()

        return self.wire_class(wire_socket)

    def stop(self):
        if self.thread:
            self.thread.join()
        self.thread = None

    def setUp(self):
        self.thread = None

    def tearDown(self):
        self.stop()

    ## tests

    def test_short_box(self):
        data = [
            """\x00\x05hello\x00\x05world\x00\x00""",
        ]
        wire = self.read_with_wire(data)
        self.assertEqual(wire.read_box(), { 'hello' : 'world' },
            "got a simple box")
        self.assertEqual(wire.read_box(), None,
            "followed by EOF")

    def test_box_in_pieces(self):
        # short timeouts here are to defeat nagle's algorithm, which would like
        # to reassemble the separate writes into a single read
        data = [
            """\x00\x05he"""
            """llo\x00"""
            """\x05world\x00\x00"""
        ]
        wire = self.read_with_wire(data)
        self.assertEqual(wire.read_box(), { 'hello' : 'world' },
            "got a simple box")
        self.assertEqual(wire.read_box(), None,
            "followed by EOF")

    def test_multiple_keys(self):
        data = [
            """\x00\x06orange\x00\x05fruit\x00\x06carrot\x00\x09vegetable\x00\x00""",
        ]
        wire = self.read_with_wire(data)
        self.assertEqual(wire.read_box(), { 'orange' : 'fruit', 'carrot' : 'vegetable' },
            "got a box with multiple keys")
        self.assertEqual(wire.read_box(), None,
            "followed by EOF")

    def test_multiple_boxes(self):
        data = [
            """\x00\x06orange\x00\x05fruit\x00\x00\x00\x06carrot\x00\x09vegetable\x00\x00""",
        ]
        wire = self.read_with_wire(data)
        self.assertEqual(wire.read_box(), { 'orange' : 'fruit' },
            "got first box")
        self.assertEqual(wire.read_box(), { 'carrot' : 'vegetable' },
            "got second box")
        self.assertEqual(wire.read_box(), None,
            "followed by EOF")

    def test_multiple_boxes_in_pieces(self):
        data = [
            """\x00\x06orange\x00""",
            """\x05fruit""",
            """\x00\x06carrot\x00\x09""",
            """veget""",
            """able\x00""",
            """\x00\x00\x06barley\x00\x05""",
            """grain\x00\x00""",
        ]
        wire = self.read_with_wire(data)
        self.assertEqual(wire.read_box(), { 'orange' : 'fruit', 'carrot' : 'vegetable' },
            "got first box")
        self.assertEqual(wire.read_box(), { 'barley' : 'grain' },
            "got second box")
        self.assertEqual(wire.read_box(), None,
            "followed by EOF")

class TestSimpleWireReading(TestWireReadingMixin, unittest.TestCase):
    wire_class = wire.SimpleWire

if __name__ == '__main__':
    unittest.main()
