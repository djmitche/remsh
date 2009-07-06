# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information

import unittest
import threading
import socket
import os
import time

from remsh.amp import wire, rpc

NAGLE_SLEEP = 0.05


class TestRPCCallsMixin(object):
    # test invoking RPC methods (call_remote)

    def get_rpc(self, responses):
        """
        Get an RPC object set up to communicate with a thread which will
        respond to each packet with the corresponding box in RESPONSES,
        remaining silent if that is None.  All boxes received are placed
        in self.received_boxes.
        """
        wire_socket, thread_sock = socket.socketpair()
        self.received_boxes = []

        def thd():
            thwire = wire.SimpleWire(thread_sock)
            for resp in responses:
                req = thwire.read_box()
                if not req:
                    break
                ask = req['_ask']
                del req['_ask']
                self.received_boxes.append(req)
                if resp:
                    resp = resp.copy()
                    if '_answer' in resp:
                        resp['_answer'] = ask
                    else:
                        resp['_error'] = ask
                    thwire.send_box(resp)
        self.thread = threading.Thread(target=thd)
        self.thread.setDaemon(1)
        self.thread.start()

        return rpc.RPC(self.wire_class(wire_socket))

    def stop(self):
        if self.thread:
            self.thread.join()
        self.thread = None

    def setUp(self):
        self.thread = None

    def tearDown(self):
        self.stop()

    ## tests

    def test_single_call_remote(self):
        rpc = self.get_rpc([
            {'_answer': None, 'sir': 'yes, sir'},
        ])
        self.failUnlessEqual(rpc.call_remote(
            'jump', howhigh='very'), {'sir': 'yes, sir'})
        self.failUnlessEqual(self.received_boxes, [
            {'_command': 'jump', 'howhigh': 'very'},
        ])

    def test_multiple_call_remote(self):
        rpc = self.get_rpc([
            {'_answer': None, 'position': 'standing'},
            {'_answer': None, 'position': 'sitting'},
        ])
        self.failUnlessEqual(
            rpc.call_remote('stand', dir='up'), {'position': 'standing'})
        self.failUnlessEqual(
            rpc.call_remote('sit', dir='down'), {'position': 'sitting'})
        self.failUnlessEqual(self.received_boxes, [
            {'_command': 'stand', 'dir': 'up'},
            {'_command': 'sit', 'dir': 'down'},
        ])

    def test_multiple_call_remote_noanswer(self):
        rpc = self.get_rpc([
            None,
            {'_answer': None, 'position': 'abdicated'},
            None,
            {'_answer': None, 'position': 'accepted'},
        ])
        self.failUnlessEqual(
            rpc.call_remote_no_answer('step', dir='around'), None)
        self.failUnlessEqual(
            rpc.call_remote('step', dir='down'), {'position': 'abdicated'})
        self.failUnlessEqual(rpc.call_remote_no_answer('step', dir='in'), None)
        self.failUnlessEqual(
            rpc.call_remote('step', dir='up'), {'position': 'accepted'})
        self.failUnlessEqual(self.received_boxes, [
            {'_command': 'step', 'dir': 'around'},
            {'_command': 'step', 'dir': 'down'},
            {'_command': 'step', 'dir': 'in'},
            {'_command': 'step', 'dir': 'up'},
        ])


class TestRPCCallsSimple(TestRPCCallsMixin, unittest.TestCase):
    wire_class = wire.SimpleWire


class TestRPCCallsResilient(TestRPCCallsMixin, unittest.TestCase):
    wire_class = wire.ResilientWire


if __name__ == '__main__':
    unittest.main()
