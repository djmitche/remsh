# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information
"""
Contains the L{Slave} class.
"""

import sys
import os
import threading

from remsh.amp import rpc


class ProtocolError(Exception):
    "An error in the internal protocol between master and slave"


class SlaveDisconnected(ProtocolError):
    "The slave disconnected in the midst of an operation"


class Slave(object):

    def __init__(self, wire, hostname, version):
        self.rpc = rpc.RPC(wire)
        self.hostname = hostname
        self.version = version

        # lock governing the connection
        self._lock = threading.Lock()

        self._disconnect_listeners = []

    # TODO: locking
    def setup(self):
        pass # does nothing by default

    def set_cwd(self, cwd=None):
        kwargs = {}
        if cwd is not None:
            kwargs['cwd'] = cwd
        resp = self.rpc.call_remote('set_cwd', **kwargs)
        return resp['cwd']

    def getenv(self):
        resp = self.rpc.call_remote('getenv')
        return dict([ (k[4:], v) for (k,v) in resp.iteritems() if k.startswith('env_') ])

    def mkdir(self, dir):
        self.rpc.call_remote('mkdir', dir=dir)

    def execute(self, args=[], stdout_cb=None, stderr_cb=None):
        self.rpc.call_remote('execute',
            args='\0'.join(args),
            want_stdout='y' if stdout_cb else 'n',
            want_stderr='y' if stderr_cb else 'n')

        # loop, handling calls without answers, until we get 'finished'
        result = {}

        def finished(rq):
            result['result'] = int(rq['result'])

        def data(rq):
            if rq['stream'] == 'stdout':
                stdout_cb(rq['data'])
            elif rq['stream'] == 'stderr':
                stderr_cb(rq['data'])

        while not result:
            self.rpc.handle_call(
                remote_finished=finished,
                remote_data=data)
        return result['result']

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

    def on_disconnect(self, callable):
        # TODO: synchronization so that this gets called immediately if
        # the slave has already disconnected?
        self._disconnect_listeners.append(callable)
