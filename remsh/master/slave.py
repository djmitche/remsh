# This file is part of remsh.
#
# remsh is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# remsh is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with remsh.  If not, see <http://www.gnu.org/licenses/>.

"""
Contains the L{Slave} class.
"""

import sys
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

    def mkdir(self, dir):
        self.rpc.call_remote('mkdir', dir=dir)

    def unlink(self, file):
        self.rpc.call_remote('unlink', file=file)

    def execute(self, args=[], stdout_cb=None, stderr_cb=None):
        self.rpc.call_remote_no_answer('execute',
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

    def on_disconnect(self, callable):
        # TODO: synchronization so that this gets called immediately if
        # the slave has already disconnected?
        self._disconnect_listeners.append(callable)
