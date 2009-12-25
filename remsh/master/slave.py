# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information
# -*- test-case-name: test.test_ops -*-

import sys
import os

class ProtocolError(Exception):
    "An error in the internal protocol between master and slave"


class NotFoundError(ProtocolError):
    "Something was not found (notfound)"


class FileExistsError(ProtocolError):
    "A file already exists (fileexists)"


class OpenFailedError(ProtocolError):
    "Open of a file on the slave failed (openfailed)"


class FailedError(ProtocolError):
    "An operation on the slave failed (failed)"


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
                except ValueError:
                    raise ProtocolError('invalid result value')
                done = True
            else:
                raise ProtocolError('unknown response box')

        return result

    def send(self, src, dest):
        # the caller is responsible for any errors from open()
        srcfile = open(src, "rb")

        error_handling = {
            'fileexists' : FileExistsError,
            'openfailed' : OpenFailedError,
            'failed' : FailedError,
        }

        self.wire.send_box({
            'meth' : 'send',
            'version' : 1,
            'dest' : dest,
        })

        box = self.wire.read_box()
        self.handle_errors(box, **error_handling)

        # write the data
        while 1:
            data = srcfile.read(65535)
            if not data:
                break
            self.wire.send_box({ 'data' : data })

        self.wire.send_box({})
        box = self.wire.read_box()
        self.handle_errors(box, **error_handling)

    def fetch(self, src, dest):
        if os.path.exists(dest):
            raise FileExistsError("Destination already exists on the master")

        # the caller is responsible for any errors from open()
        destfile = open(dest, "wb")

        error_handling = {
            'notfound' : NotFoundError,
            'openfailed' : OpenFailedError,
            'failed' : FailedError,
        }

        self.wire.send_box({
            'meth' : 'fetch',
            'version' : 1,
            'src' : src
        })

        while True:
            box = self.wire.read_box()
            if box == {}:
                break
            self.handle_errors(box, **error_handling)
            if 'data' not in box:
                raise ProtocolError('not a data box')
            try:
                destfile.write(box['data'])
            except IOError:
                # read and ignore the rest of the data, then raise the exception
                while True:
                    box = self.wire.read_box()
                    self.handle_errors(box, **error_handling)
                    if box == {}:
                        raise

    def remove(self, path):
        box = { 'meth' : 'remove', 'version' : 1, 'path' : path }
        self.wire.send_box(box)
        box = self.wire.read_box()
        self.handle_errors(box,
            failed=FailedError)

    def rename(self, src, dest):
        box = { 'meth' : 'rename', 'version' : 1, 'src' : src, 'dest' : dest }
        self.wire.send_box(box)
        box = self.wire.read_box()
        self.handle_errors(box,
            fileexists=FileExistsError,
            notfound=NotFoundError,
            failed=FailedError)

    def copy(self, src, dest):
        box = { 'meth' : 'copy', 'version' : 1, 'src' : src, 'dest' : dest }
        self.wire.send_box(box)
        box = self.wire.read_box()
        self.handle_errors(box,
            fileexists=FileExistsError,
            notfound=NotFoundError,
            failed=FailedError)

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
