# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information

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
        """
        Make a socket to which each string in WRITES is written, separated by
        apause long enough to avoid invoking Nagle's algorithm.
        """
        wire_socket, thread_sock = socket.socketpair()

        def thd():
            for wr in writes:
                thread_sock.sendall(wr)
                time.sleep(NAGLE_SLEEP)
            thread_sock.close()
        self.thread = threading.Thread(target=thd)
        self.thread.setDaemon(1)
        self.thread.start()

        self.wire = self.wire_class(wire_socket)
        return self.wire

    def stop(self):
        if self.thread:
            self.thread.join()
        self.thread = None
        if self.wire:
            self.wire.stop()

    def setUp(self):
        self.wire = None
        self.thread = None

    def tearDown(self):
        self.stop()

    ## tests

    def test_short_box(self):
        data = [
            """\x00\x05hello\x00\x05world\x00\x00""",
        ]
        wire = self.read_with_wire(data)
        self.failUnlessEqual(wire.read_box(), {'hello': 'world'})
        self.failUnlessEqual(wire.read_box(), None)

    def test_box_in_pieces(self):
        # short timeouts here are to defeat nagle's algorithm, which would like
        # to reassemble the separate writes into a single read
        data = [
            """\x00\x05he"""
            """llo\x00"""
            """\x05world\x00\x00""",
        ]
        wire = self.read_with_wire(data)
        self.failUnlessEqual(wire.read_box(), {'hello': 'world'})
        self.failUnlessEqual(wire.read_box(), None)

    def test_multiple_keys(self):
        data = [
            """\x00\x06orange\x00\x05fruit\x00\x06carrot\x00\x09vegetable\x00\x00""",
        ]
        wire = self.read_with_wire(data)
        self.failUnlessEqual(wire.read_box(), {'orange': 'fruit', 'carrot': 'vegetable'})
        self.failUnlessEqual(wire.read_box(), None)

    def test_multiple_boxes(self):
        data = [
            """\x00\x06orange\x00\x05fruit\x00\x00\x00\x06carrot\x00\x09vegetable\x00\x00""",
        ]
        wire = self.read_with_wire(data)
        self.failUnlessEqual(wire.read_box(), {'orange': 'fruit'})
        self.failUnlessEqual(wire.read_box(), {'carrot': 'vegetable'})
        self.failUnlessEqual(wire.read_box(), None)

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
        self.failUnlessEqual(wire.read_box(), {'orange': 'fruit', 'carrot': 'vegetable'})
        self.failUnlessEqual(wire.read_box(), {'barley': 'grain'})
        self.failUnlessEqual(wire.read_box(), None)


class TestSimpleWireReading(TestWireReadingMixin, unittest.TestCase):
    wire_class = wire.SimpleWire


class TestResilientWireReading(TestWireReadingMixin, unittest.TestCase):
    wire_class = wire.ResilientWire


class TestWireWritingMixin(object):
    # test writing packets with ampwire; the mixin uses self.wire_class as the
    # class to test

    def write_to_wire(self, boxes):
        """
        Write boxes using the appropriate wire_class, and return the resulting
        bytes from the socket.
        """
        result_socket, thread_sock = socket.socketpair()

        def thd():
            wire = self.wire_class(thread_sock)
            for box in boxes:
                wire.send_box(box)
            wire.stop()
            thread_sock.close()
        thread = threading.Thread(target=thd)
        thread.setDaemon(1)
        thread.start()

        buf = ''
        while 1:
            d = result_socket.recv(1024)
            if not d:
                break
            buf += d
        thread.join()
        return buf

    ## tests

    def test_short_box(self):
        self.failUnlessEqual(self.write_to_wire([
            {'hello': 'world'},
        ]), """\x00\x05hello\x00\x05world\x00\x00""")

    def test_two_boxes(self):
        self.failUnlessEqual(self.write_to_wire([
            {'hello': 'world'},
            {'hola': 'compadre'},
        ]), """\x00\x05hello\x00\x05world\x00\x00\x00\x04hola\x00\x08compadre\x00\x00""")
    def test_multiple_keys(self):
        # multiple keys can render differently depending on the dict ordering
        self.failUnless(self.write_to_wire([
            {'hello': 'world', 'world_mood': 'grumpy'},
        ]) in (
            """\x00\x05hello\x00\x05world\x00\x0aworld_mood\x00\x06grumpy\x00\x00""",
            """\x00\x0aworld_mood\x00\x06grumpy\x00\x05hello\x00\x05world\x00\x00""",
        ))


class TestSimpleWireWriting(TestWireWritingMixin, unittest.TestCase):
    wire_class = wire.SimpleWire


class TestResilientWireWriting(TestWireWritingMixin, unittest.TestCase):
    wire_class = wire.ResilientWire


if __name__ == '__main__':
    unittest.main()
