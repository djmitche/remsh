# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information
# -*- test-case-name: test.test_ops -*-

import sys
import os

class ProtocolError(Exception):
    "An error in the internal protocol between master and slave"


class NotFoundError(ProtocolError):
    "Error code 'notfound'"


class SlaveDisconnected(ProtocolError):
    "The slave disconnected in the midst of an operation"

# utility function
def bool(b):
    if b: return 'y'
    return 'n'


class Slave(object):

    def __init__(self, wire):
        self.wire = wire

        # TODO: ???
        self._disconnect_listeners = []

    def set_cwd(self, cwd=None):
        box = { 'meth' : 'set_cwd', 'version' : 1 }
        if cwd is not None:
            box['cwd'] = cwd
        self.wire.send_box(box)
        box = self.wire.read_box()
        self.handle_errors(box,
            notfound=NotFoundError)
        return box['cwd']

    def getenv(self):
        box = { 'meth' : 'getenv', 'version' : 1 }
        self.wire.send_box(box)
        box = self.wire.read_box()
        self.handle_errors(box)
        return dict([ (k[4:], v) for (k,v) in box.iteritems() if k.startswith('env_') ])

    def mkdir(self, dir):
        box = { 'meth' : 'mkdir', 'version' : 1, 'dir' : dir }
        self.wire.send_box(box)
        box = self.wire.read_box()
        self.handle_errors(box)

    def execute(self, args=[], stdout_cb=None, stderr_cb=None):
        box = {
            'meth' : 'execute',
            'version' : 1,
            'args' : '\0'.join(args),
            'want_stdout' : bool(stdout_cb),
            'want_stderr' : bool(stderr_cb),
        }
        self.wire.send_box(box)

        # loop, handling calls without answers, until we get 'finished'
        def finished(rq):
            result['result'] = int(rq['result'])

        def data(rq):
            if rq['stream'] == 'stdout':
                stdout_cb(rq['data'])
            elif rq['stream'] == 'stderr':
                stderr_cb(rq['data'])

        done = False
        while not done:
            box = self.wire.read_box()
            self.handle_errors(box)
            if 'stream' in box:
                stream = box['stream']
                if 'data' not in box:
                    raise ProtocolError('stream box without data')
                data = box['data']
                if stdout_cb and stream == 'stdout':
                    stdout_cb(data)
                elif stderr_cb and stream == 'stderr':
                    stderr_cb(data)
                else:
                    raise ProtocolError('got data for unknown stream')
            elif 'result' in box:
                try:
                    result = int(box['result'])
                except:
                    raise ProtocolError('invalid result value')
                done = True
            else:
                raise ProtocolError('unknown response box')

        return result

    def send(self, src, dest):
        # the caller is responsible for any errors from open()
        srcfile = open(src, "rb")
        self.rpc.call_remote('send',
            dest=dest)

        # write the data
        while 1:
            data = srcfile.read(65535)
            if not data:
                break
            self.rpc.call_remote_no_answer('data',
                data=data)

        # this may raise a RemoteError if the slave had trouble writing
        self.rpc.call_remote('finished')

    def fetch(self, src, dest):
        if os.path.exists(dest):
            raise rpc.RemoteError("'%s' already exists on the master" % dest)

        # the caller is responsible for any errors from open()
        destfile = open(dest, "wb")

        self.rpc.call_remote('fetch',
            src=src)

        # loop, handling data and finished calls
        state = {'done': False, 'errmsg': None, 'localerr': None}

        def data(rq):
            if state['localerr']:
                return
            try:
                destfile.write(rq['data'])
            except Exception, e:
                state['localerr'] = e

        def finished(rq):
            if 'errmsg' in rq:
                state['errmsg'] = rc['errmsg']
            state['done'] = True

        while not state['done']:
            self.rpc.handle_call(
                remote_finished=finished,
                remote_data=data)
        if state['errmsg']:
            raise rpc.RemoteError(state['errmsg'])
        elif state['localerr']:
            raise state['localerr']

    def remove(self, path):
        self.rpc.call_remote('remove', path=path)

    def rename(self, src, dest):
        self.rpc.call_remote('rename', src=src, dest=dest)

    def copy(self, src, dest):
        self.rpc.call_remote('copy', src=src, dest=dest)

    def stat(self, pathname):
        resp = self.rpc.call_remote('stat', pathname=pathname)
        if resp['result']:
            return resp['result']

    ## utilities

    standard_errors = {
        'invalid-meth' : ProtocolError,
        'version-too-new' : ProtocolError,
        'version-unsupported' : ProtocolError,
        'invalid' : ProtocolError,
        'unknown' : RuntimeError,
    }

    def handle_errors(self, box, **more_errcodes):
        if box is None:
            raise ProtocolError("unexpected EOF during operation")

        if 'error' not in box:
            return

        if 'errtag' not in box: box['errtag'] = 'unknown'
        errtag = box['errtag']
        exc_cls = more_errcodes.get(errtag)
        if not exc_cls:
            exc_cls = self.standard_errors.get(errtag)
        if not exc_cls:
            exc_cls = self.standard_errors.get('unknown')

        raise exc_cls(box['error'])

    def on_disconnect(self, callable):
        # TODO: synchronization so that this gets called immediately if
        # the slave has already disconnected?
        self._disconnect_listeners.append(callable)
