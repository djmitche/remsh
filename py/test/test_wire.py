# This file is part of remsh
# Copyright 2009, 2010 Dustin J. Mitchell
# See COPYING for license information

import unittest
import threading
import os
import time

from remsh.xport.local import LocalXport
from remsh.wire import Wire


class TestWireReading(unittest.TestCase):
    """

    test reading packets from the xport layer

    """

    def read_with_wire(self, writes):
        wire_xport, thread_xport = LocalXport.create()

        def thd():
            for wr in writes:
                thread_xport.write(wr)
            thread_xport.close()
        self.thread = threading.Thread(target=thd)
        self.thread.setDaemon(1)
        self.thread.start()

        self.wire = Wire(wire_xport)
        return self.wire

    def stop(self):
        if self.thread:
            self.thread.join()
        self.thread = None
        if self.wire:
            self.wire.close()

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
            """\x00\x06orange\x00\x05fruit"""
            + """\x00\x06carrot\x00\x09vegetable\x00\x00""",
        ]
        wire = self.read_with_wire(data)
        self.failUnlessEqual(wire.read_box(),
            {'orange': 'fruit', 'carrot': 'vegetable'})
        self.failUnlessEqual(wire.read_box(), None)

    def test_multiple_boxes(self):
        data = [
            """\x00\x06orange\x00\x05fruit\x00\x00"""
            + """\x00\x06carrot\x00\x09vegetable\x00\x00""",
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
        self.failUnlessEqual(wire.read_box(),
            {'orange': 'fruit', 'carrot': 'vegetable'})
        self.failUnlessEqual(wire.read_box(),
            {'barley': 'grain'})
        self.failUnlessEqual(wire.read_box(),
            None)


class TestWireWriting(unittest.TestCase):
    """

    test writing packets to the xport layer

    """

    def write_to_wire(self, boxes):
        result_xport, thread_xport = LocalXport.create()

        def thd():
            wire = Wire(thread_xport)
            for box in boxes:
                wire.send_box(box)
            wire.close()
        thread = threading.Thread(target=thd)
        thread.setDaemon(1)
        thread.start()

        buf = ''
        while 1:
            d = result_xport.read()
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
        ]), """\x00\x05hello\x00\x05world\x00\x00"""
            + """\x00\x04hola\x00\x08compadre\x00\x00""")

    def test_multiple_keys(self):
        # multiple keys can render differently depending on the dict ordering
        self.failUnless(self.write_to_wire([
            {'hello': 'world', 'world_mood': 'grumpy'},
        ]) in (
            """\x00\x05hello\x00\x05world"""
                + """\x00\x0aworld_mood\x00\x06grumpy\x00\x00""",
            """\x00\x0aworld_mood\x00\x06grumpy"""
                + """\x00\x05hello\x00\x05world\x00\x00""",
        ))


if __name__ == '__main__':
    unittest.main()
