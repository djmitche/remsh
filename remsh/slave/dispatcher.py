# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information
# -*- test-case-name: test.test_ops -*-

import os
import sys
import socket
import subprocess
import select
import shutil
import errno
import stat

class RemoteError(Exception):
    """
    
    Utility exception for sending error boxes
    
    """

    def __init__(self, errtag, error):
        self.errbox = {
            'errtag' : errtag,
            'error' : error }


class InvalidRequestError(RemoteError):
    """

    An 'invalid' RemoteError

    """

    def __init__(self):
        RemoteError.__init__(self, 'invalid', 'invalid format for this method')

# contains pointers to the SlaveServer methods for each operation, in a
# two-level dictionary by key and then version.  This has to be global
# during parsing, but is made a class variable below
op_methods = {}


class SlaveServer(object):

    def __init__(self, wire):
        self.wire = wire
        self.default_wd = os.getcwd()

    # decorator for op methods
    def op_method(name, version=1):
        def wrap(f):
            meth_dict = op_methods.setdefault(name, {})
            assert version not in meth_dict
            meth_dict[version] = f
            return f
        return wrap

    # include op_methods in the class scope
    op_methods = op_methods

    ## main method

    def serve(self):
        while 1:
            box = self.wire.read_box()
            if box is None: break

            if 'meth' not in box or 'version' not in box: 
                self.wire.send_box({ 'error' : 'invalid request',
                                     'errtag' : 'invalid'})
                continue

            meth = box['meth']
            if meth not in self.op_methods:
                self.wire.send_box({ 'error' : 'unknown method',
                                     'errtag' : 'invalid-meth'})
                continue

            try:
                version = int(box['version'])
            except:
                self.wire.send_box({ 'error' : 'invalid request',
                                     'errtag' : 'invalid'})
                continue

            meth_dict = self.op_methods[meth]
            if version not in meth_dict:
                # find out if the version was too new or too old
                supported_versions = meth_dict.keys()
                supported_versions.sort()
                if version > supported_versions[-1]:
                    self.wire.send_box(
                        { 'error' : 'version too new (highest supported: %d)'
                                                    % supported_versions[-1],
                          'errtag' : 'version-too-new'})
                else:
                    self.wire.send_box(
                        { 'error' : 'version not supported',
                          'errtag' : 'version-unsupported'})
                continue

            # finally, we can actually execute the method!
            try:
                meth_dict[version](self, box)
            except RemoteError, e:
                self.wire.send_box(e.errbox)

    ## operations

    @op_method('set_cwd', 1)
    def remote_set_cwd(self, box):
        cwd = box.get('cwd')
        if cwd is None:
            cwd = self.default_wd

        if cwd:
            try:
                os.chdir(cwd)
            except OSError, e:
                raise RemoteError('notfound', e.strerror)

        cwd = os.getcwd()
        self.wire.send_box({'cwd': cwd})

    @op_method('getenv', 1)
    def remote_getenv(self, box):
        resp = dict([ ('env_%s' % k, v[:65535]) for (k,v) in os.environ.iteritems() ])
        self.wire.send_box(resp)

    @op_method('mkdir', 1)
    def remote_mkdir(self, box):
        if 'dir' not in box:
            raise InvalidRequestError()

        dir = box['dir']

        if not os.path.exists(dir):
            try:
                os.makedirs(dir)
            except OSError, e:
                raise RemoteError('unknown', e.strerror)
        self.wire.send_box({})

    @op_method('execute', 1)
    def remote_execute(self, box):
        for k in 'want_stdout want_stderr args'.split():
            if k not in box:
                raise InvalidRequestError()
        want_stdout = self._getbool(box, 'want_stdout')
        want_stderr = self._getbool(box, 'want_stderr')
        args = box['args'].split('\0')

        # run the command
        null = open("/dev/null", "r+")
        if want_stdout:
            stdout = subprocess.PIPE
        else:
            stdout = null
        if want_stderr:
            stderr = subprocess.PIPE
        else:
            stderr = null
        try:
            proc = subprocess.Popen(args=args,
                stdin=null, stdout=stdout, stderr=stderr,
                universal_newlines=False)
        except Exception, e:
            # TODO: more explicit
            raise RemoteError('execfail', `e`)

        # now use select to watch those files, with a short timeout to watch
        # for process exit (this timeout grows up to 1 second)
        timeout = 0.01
        readfiles = []
        if want_stdout:
            readfiles.append(proc.stdout)
        if want_stderr:
            readfiles.append(proc.stderr)
        while 1:
            rlist, wlist, xlist = select.select(readfiles, [], [], timeout)
            timeout = min(1.0, timeout * 2)

            def send(file, name):
                data = file.read(65535)
                if not data:
                    readfiles.remove(file)
                else:
                    self.wire.send_box({
                        'data' : data,
                        'stream' : name,
                    })
            if proc.stdout in rlist:
                send(proc.stdout, 'stdout')
            if proc.stderr in rlist:
                send(proc.stderr, 'stderr')
            if not rlist and proc.poll() is not None:
                break
        self.wire.send_box({
            'result' : proc.returncode
        })

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
        self.wire.send_box({})

        # now handle data() calls until we get a 'finished', using a dictionary
        # to store state (due to Python's problems with nested lexical scopes)
        state = {'done': False, 'error': False}

        def remote_data(rq):
            if state['error']:
                return
            try:
                file.write(rq['data'])
            except Exception, e:
                state['error'] = e

        def remote_finished(rq):
            state['done'] = True
            if state['error']:
                raise state['error']
            file.close()
            self.wire.send_box({})

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
        self.wire.send_box({})

        # now *make* data() calls until EOF
        state = {'error': False}

        while 1:
            try:
                data = file.read(65535)
            except Exception, e:
                state['error'] = e
                break
            if not data:
                break
            self.call_remote_no_answer('data',
                    data=data)

        file.close()
        if state['error']:
            self.call_remote('finished',
                errstr=str(state['error']))
        else:
            self.call_remote('finished')

    def remote_remove(self, rq):
        path = rq['path']

        if os.path.exists(path):
            if os.path.isdir(path):
                try:
                    shutil.rmtree(path)
                except OSError, e:
                    # this error may be due to directory permissions;
                    # do a recursive chmod 0700 and try again
                    for root, dirs, files in os.walk(path):
                        for d in dirs:
                            os.chmod(os.path.join(root, d), 0700)
                    try:
                        shutil.rmtree(path)
                    except OSError, e:
                        raise RemoteError(e.strerror)

                if os.path.exists(path):
                    raise RemoteError("tree not removed")
            else:
                try:
                    os.unlink(path)
                except OSError, e:
                    raise RemoteError(e.strerror)

        self.wire.send_box({})

    def remote_rename(self, rq):
        src = rq['src']
        dest = rq['dest']

        if not os.path.exists(src):
            raise RemoteError("'%s' does not exist" % src)
        if os.path.exists(dest):
            raise RemoteError("'%s' already exists" % dest)

        try:
            os.rename(src, dest)
        except OSError, e:
            raise RemoteError(e.strerror)

        self.wire.send_box({})

    def remote_copy(self, rq):
        src = rq['src']
        dest = rq['dest']

        if not os.path.exists(src):
            raise RemoteError("'%s' does not exist" % src)
        if os.path.exists(dest):
            raise RemoteError("'%s' already exists" % dest)

        try:
            shutil.copyfile(src, dest)
        except OSError, e:
            raise RemoteError(e.strerror)
        except Exception, e:
            raise RemoteError(str(e))

        self.wire.send_box({})

    def remote_stat(self, rq):
        pathname = rq['pathname']

        try:
            st = os.stat(pathname)
        except OSError, e:
            if e.errno == errno.ENOENT:
                self.wire.send_box({'result' : ''})
                return
            raise RemoteError(e.strerror)

        if stat.S_ISDIR(st.st_mode):
            self.wire.send_box({'result' : 'd'})
        else:
            self.wire.send_box({'result' : 'f'})

    def _getbool(self, rq, name):
        if name not in rq or rq[name] not in 'ny':
            raise RemoteError('invalid', "invalid boolean value")
        return rq[name] == 'y'

# delete op_methods from the global scope; it's not needed anymore
del op_methods
