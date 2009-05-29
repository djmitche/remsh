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

class ProtocolError(Exception):
    "An error in the internal protocol between master and slave"

class SlaveDisconnected(ProtocolError):
    "The slave disconnected in the midst of an operation"

class Slave(object):
    def __init__(self, ampconn, hostname, version):
        self.ampconn = ampconn
        self.hostname = hostname
        self.version = version

        # lock governing the connection
        self._lock = threading.Lock()

        self._disconnect_listeners = []

    def _do_transaction(self, command, data_cb):
        """
        For use by subclasses.  Send ``command``, which is an iterable of
        boxes, to the slave, call ``data_cb`` with each data box the slave
        sends, and then return the ``opdone`` box.  This method acquires and
        subsequently releases the slave.  Any errors -- protocol or otherwise
        -- are raised as exceptions.
        """
        self._lock.acquire()
        # TODO: better detection of SlaveDisconnected: EOFError?
        # TODO: handle on_disconnect
        # TODO: timeout
        try:
            # send the command boxes
            for box in command:
                self.ampconn.send_box(box)

            # and read the results
            while 1:
                box = self.ampconn.read_box()
                if not box: raise SlaveDisconnected("slave disconnected while running a command")
                if box['type'] == 'data':
                    data_cb(box)
                elif box['type'] == 'opdone':
                    return box
        finally:
            self._lock.release()

    ##
    # ISlave methods

    def setup(self):
        pass # does nothing by default

    def set_cwd(self, new_cwd):
        command = [ {'type' : 'newop', 'op' : 'set_cwd'}, ]
        if new_cwd is not None:
            command.append({'type' : 'opparam', 'param' : 'cwd', 'value' : new_cwd})
        command.append({'type' : 'startop'})

        resbox = self._do_transaction(command, None)

        if 'cwd' in resbox:
            return resbox['cwd']
        else:
            raise OSError(resbox['error'])

    def mkdir(self, dir):
        command = [
            {'type' : 'newop', 'op' : 'mkdir'},
            {'type' : 'opparam', 'param' : 'dir', 'value' : dir},
            {'type' : 'startop'},
        ]
        resbox = self._do_transaction(command, None)

        if 'error' in resbox: raise OSError(resbox['error'])
        return

    def unlink(self, file):
        command = [
            {'type' : 'newop', 'op' : 'unlink'},
            {'type' : 'opparam', 'param' : 'file', 'value' : file},
            {'type' : 'startop'},
        ]
        resbox = self._do_transaction(command, None)

        if 'error' in resbox: raise OSError(resbox['error'])
        return

    def execute(self, args=[], stdout_cb=None, stderr_cb=None):
        def data_cb(box):
            if box['name'] == 'stdout': stdout_cb(box['data'])
            elif box['name'] == 'stderr': stderr_cb(box['data'])
            else: raise RuntimeError("unknown stream '%s'" % box['name'])

        resbox = self._do_transaction([
            {'type' : 'newop', 'op' : 'execute'},
        ] + [
            {'type' : 'opparam', 'param' : 'arg', 'value' : arg}
            for arg in args
        ] + [
            {'type' : 'startop'}
        ], data_cb)

        return int(resbox['result'])

    def on_disconnect(self, callable):
        # TODO: synchronization so that this gets called immediately if
        # the slave has already disconnected?
        self._disconnect_listeners.append(callable)
