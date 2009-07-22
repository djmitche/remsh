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


# conversation elements for get_rpc, below
class WaitForIncoming:
    def __init__(self, response=None):
        self.response = response

class SendBox:
    def __init__(self, box):
        self.box = box

class TestRPCCallsMixin(object):
    # test invoking RPC methods (call_remote)

    def get_rpc(self, convo):
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
            for step in convo:
                if isinstance(step, WaitForIncoming):
                    req = thwire.read_box()
                    if not req:
                        break
                    if '_ask' in req:
                        ask = req['_ask']
                        del req['_ask']
                    self.received_boxes.append(req)
                    if step.response:
                        resp = step.response.copy()
                        if '_answer' in resp:
                            resp['_answer'] = ask
                        else:
                            resp['_error'] = ask
                        thwire.send_box(resp)
                else:
                    thwire.send_box(step.box)

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
            WaitForIncoming({'_answer': None, 'sir': 'yes, sir'}),
        ])
        self.failUnlessEqual(rpc.call_remote(
            'jump', howhigh='very'), {'sir': 'yes, sir'})
        self.failUnlessEqual(self.received_boxes, [
            {'_command': 'jump', 'howhigh': 'very'},
        ])

    def test_multiple_call_remote(self):
        rpc = self.get_rpc([
            WaitForIncoming({'_answer': None, 'position': 'standing'}),
            WaitForIncoming({'_answer': None, 'position': 'sitting'}),
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
            WaitForIncoming(),
            WaitForIncoming({'_answer': None, 'position': 'abdicated'}),
            WaitForIncoming(),
            WaitForIncoming({'_answer': None, 'position': 'accepted'}),
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

    def test_handle_call(self):
        rpc = self.get_rpc([
            SendBox({'_ask' : '12', '_command' : 'sit', 'where' : 'down'}),
            SendBox({'_ask' : '13', '_command' : 'state', 'what' : 'name'}),
            WaitForIncoming(),
            SendBox({'_ask' : '14', '_command' : 'state', 'what' : 'rank'}),
            WaitForIncoming(),
            SendBox({'_ask' : '15', '_command' : 'go', 'where' : 'away'}),
            WaitForIncoming(),
        ])

        sent_boxes = []
        def remote_sit(box):
            sent_boxes.append(box)
        def remote_state(box):
            sent_boxes.append(box)
            if box['what'] == 'name':
                rpc.send_response({'name' : 'remsh'})
            elif box['what'] == 'rank':
                rpc.send_response({'name' : 'kernel'})
        def remote_go(box):
            sent_boxes.append(box)
            rpc.send_response({})

        for _ in range(4):
            rpc.handle_call(
                remote_sit = remote_sit, 
                remote_state = remote_state, 
                remote_go = remote_go)

        self.stop()

        self.failUnlessEqual(sent_boxes, [
            {'where': 'down'},
            {'what': 'name'},
            {'what': 'rank'},
            {'where': 'away'},
        ])
        self.failUnlessEqual(self.received_boxes, [
            {'_answer': '13', 'name': 'remsh'},
            {'_answer': '14', 'name': 'kernel'},
            {'_answer': '15'},
        ])


class TestRPCCallsSimple(TestRPCCallsMixin, unittest.TestCase):
    wire_class = wire.SimpleWire


class TestRPCCallsResilient(TestRPCCallsMixin, unittest.TestCase):
    wire_class = wire.ResilientWire


if __name__ == '__main__':
    unittest.main()
