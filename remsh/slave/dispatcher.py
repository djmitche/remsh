# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information

import os
import sys
import socket
import subprocess
import select

from remsh.amp.rpc import RPC, RemoteError

class SlaveRPC(RPC):
    def __init__(self, wire):
        RPC.__init__(self, wire)
        self.default_wd = os.getcwd()

    def remote_set_cwd(self, rq):
        cwd = rq.get('cwd')
        if cwd is None:
            cwd = self.default_wd

        if cwd:
            try:
                os.chdir(cwd)
            except OSError, e:
                raise RemoteError(e.strerror)

        cwd = os.getcwd()
        self.send_response({ 'cwd' : cwd })

    def remote_mkdir(self, rq):
        dir = rq['dir']

        if not os.path.exists(dir):
            try:
                os.makedirs(dir)
            except OSError, e:
                raise RemoteError(e.strerror)

        self.send_response({})

    def remote_unlink(self, rq):
        file = rq['file']

        try:
            os.unlink(file)
        except OSError, e:
            raise RemoteError(e.strerror)

        self.send_response({})

    def remote_execute(self, rq):
        want_stdout = self._getbool(rq, 'want_stdout')
        want_stderr = self._getbool(rq, 'want_stderr')
        args = rq['args'].split('\0')
        
        # run the command
        null = open("/dev/null", "r+")
        stdout = subprocess.PIPE if want_stdout else null
        stderr = subprocess.PIPE if want_stderr else null
        try:
            proc = subprocess.Popen(args=args,
                stdin=null, stdout=stdout, stderr=stderr,
                universal_newlines=False)
        except Exception, e:
            raise RemoteError(`e`)

        # we can send a response now, as (hopefully) everything that could
        # raise RemoteError has been done
        self.send_response({})

        # now use select to watch those files, with a short timeout to watch
        # for process exit (this timeout grows up to 1 second)
        timeout = 0.01
        readfiles = []
        if want_stdout: readfiles.append(proc.stdout)
        if want_stderr: readfiles.append(proc.stderr)
        while 1:
            rlist, wlist, xlist = select.select(readfiles, [], [], timeout)
            timeout = min(1.0, timeout * 2)
            def send(file, name):
                data = file.read(65535)
                if not data:
                    readfiles.remove(file)
                else:
                    self.call_remote_no_answer('data', stream=name, data=data)
            if proc.stdout in rlist: send(proc.stdout, 'stdout')
            if proc.stderr in rlist: send(proc.stderr, 'stderr')
            if not rlist and proc.poll() is not None: break
        self.call_remote_no_answer('finished', result=proc.returncode)

    def remote_send(self, rq):
        dest = rq['dest']
        
        # try to open the file for writing
        if os.path.exists(dest):
            raise RemoteError("File '%s' already exists" % dest)
        try:
            file = open(dest, "wb") # TODO: support non-binary
        except IOError, e:
            raise RemoteError(e.strerror)

        # we can send a response now, as (hopefully) everything that could
        # raise RemoteError has been done, except for the
        self.send_response({})

        # now handle data() calls until we get a 'finished', using a dictionary
        # to store state (due to Python's problems with nested lexical scopes)
        state = { 'done' : False, 'error' : False }

        def remote_data(rq):
            if state['error']: return
            try:
                file.write(rq['data'])
            except Exception, e:
                state['error'] = e

        def remote_finished(rq):
            state['done'] = True
            if state['error']: raise state['error']
            file.close()
            self.send_response({})
            
        while not state['done']:
            self.handle_call(
                remote_data=remote_data,
                remote_finished=remote_finished)

    def remote_fetch(self, rq):
        src = rq['src']
        
        # try to open the file for reading
        if not os.path.exists(src):
            raise RemoteError("File '%s' does not exist" % src)
        try:
            file = open(src, "rb") # TODO: support non-binary
        except IOError, e:
            raise RemoteError(e.strerror)

        # we can send a response now
        self.send_response({})

        # now *make* data() calls until EOF
        state = { 'error' : False }

        while 1:
            try:
                data = file.read(65535)
            except Exception, e:
                state['error'] = e
                break
            if not data: break
            self.call_remote_no_answer('data',
                    data=data)
        
        file.close()
        if state['error']:
            self.call_remote('finished',
                    errstr=str(state['error']))
        else:
            self.call_remote('finished')

    def _getbool(self, rq, name):
        if name not in rq or rq[name] not in 'ny':
            raise RuntimeError("invalid boolean value")
        return rq[name] == 'y'

# TODO: figure out what to do about registration
def run(wire):
    """
    Run a slave on ``wire``, a L{wire.SimpleWire} object.  This function
    returns if the remote end disconnects cleanly.
    """
    wire.send_box({'type' : 'register', 'hostname' : socket.gethostname(), 'version' : 1})
    box = wire.read_box()
    if not box or box['type'] != 'registered':
        raise RuntimeError("expected a 'registered' box, got %s" % (box,))

    rpc = SlaveRPC(wire)
    while 1:
        rpc.handle_call()
