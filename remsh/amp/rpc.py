# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information

from remsh.amp import wire

Error = wire.Error


class RemoteError(Exception):
    """An error sent directly from the remote system"""


class RPC(object):

    def __init__(self, wire):
        self.wire = wire
        self.counter = 1

    ##
    # Public interface

    def call_remote(self, method, **kwargs):
        return self._call_remote(method, True, kwargs)

    def call_remote_no_answer(self, method, **kwargs):
        return self._call_remote(method, False, kwargs)

    def handle_call(self, **handlers):
        reqbox = self.wire.read_box()
        if not reqbox:
            return
        if '_ask' not in reqbox:
            raise Error("request box does not have an _ask key")
        ask_token = reqbox['_ask']
        del reqbox['_ask']

        if '_command' not in reqbox:
            raise Error("request box does not have a _command key")
        methname = 'remote_' + reqbox['_command']
        if methname in handlers:
            meth = handlers[methname]
        else:
            if not hasattr(self, methname):
                raise Error("unknown command %r" % reqbox['_command'])
            meth = getattr(self, methname)
        del reqbox['_command']

        self.sent_response = False
        self.ask_token = ask_token
        try:
            meth(reqbox)
        except RemoteError, e:
            if self.sent_response:
                raise RuntimeError(
                    "subclasses shouldn't raise RemoteError after a response!")
            respbox = {'_error': ask_token, '_error_description': e.args[0],
                '_error_code': '0'}
            self.wire.send_box(respbox)
            return

    def send_response(self, respbox):
        if self.sent_response:
            raise RuntimeError("cannot send more than one response")
        self.sent_response = True
        respbox['_answer'] = self.ask_token
        self.wire.send_box(respbox)

    ##
    # Implementation

    # TODO: add mutual exclusion here? or at the wire level? or at all?
    # -> probaby here, because counter is unprotected

    def _call_remote(self, method, expect_answer, arguments):
        ask = str(self.counter)
        self.counter += 1

        wirebox = arguments.copy()
        wirebox['_command'] = method
        wirebox['_ask'] = ask
        self.wire.send_box(wirebox)

        if not expect_answer:
            return

        respbox = self.wire.read_box()
        if not respbox:
            raise Error("Unexpected EOF")
        if '_answer' in respbox:
            if respbox['_answer'] != ask:
                raise Error("answer box does not correspond to the request")
            del respbox['_answer']
            return respbox
        elif '_error' in respbox:
            if respbox['_error'] != ask:
                raise Error("error box does not correspond to the request")
            raise RemoteError(respbox['_error_description'])
        else:
            raise Error("response has neither _answer nor _error keys")
