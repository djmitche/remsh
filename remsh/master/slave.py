# This file is part of Remsh.
#
# Remsh is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Remsh is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Remsh.  If not, see <http://www.gnu.org/licenses/>.

"""
Contains the L{Slave} class.
"""

import sys
import threading

from zope.interface import implements

from remsh import interfaces

class ProtocolError(Exception):
    "An error in the internal protocol between master and slave"

class SlaveDisconnected(ProtocolError):
    "The slave disconnected in the midst of an operation"

class Slave(object):
    """
    I am the most basic implementation of L{ISlave}, providing all of the
    required methods.  I am a subclass of L{threading.Thread}, and my thread is
    used for blocking communication with the other end of the
    L{simpleamp.Connection}.

    I am intended to be subclassed to add additional functionality.
    Overridable methods and hooks are described as such in their docstrings.

    @ivar ampconn: Connection to the remote system.  This is governed by the
    acquire() and relase() methods.
    @type ampconn: L{simpleamp.Connection}

    @ivar hostname: hostname received in the initial 'register' box
    @type hostname: string

    @ivar version: version of the remote system, as received in the 'register' box
    @type version: integer
    """

    implements(interfaces.ISlave)

    def __init__(self, ampconn, hostname, version):
        self.ampconn = ampconn
        self.hostname = hostname
        self.version = version

        # used by acquire() and release()
        self.lock = threading.Lock()

        self._disconnect_listeners = []

    def do_transaction(self, command, data_cb):
        """
        For use by subclasses.  Send ``command``, which is an iterable of
        boxes, to the slave, call ``data_cb`` with each data box the slave
        sends, and then return the ``opdone`` box.  This method acquires and
        subsequently releases the slave.  Any errors -- protocol or otherwise
        -- are raised as exceptions.
        """
        self.acquire()
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
            self.release()

    def acquire(self):
        """
        Lock this slave, giving exclusive access to its connection.
        """
        self.lock.acquire()

    def release(self):
        """
        Release this slave, allowing other threads to use it.
        """
        self.lock.release()

    ##
    # ISlave methods

    def setup(self):
        pass # does nothing by default

    def set_cwd(self, new_cwd):
        command = [ {'type' : 'newop', 'op' : 'set_cwd'}, ]
        if new_cwd is not None:
            command.append({'type' : 'opparam', 'param' : 'cwd', 'value' : new_cwd})
        command.append({'type' : 'startop'})

        resbox = self.do_transaction(command, None)

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
        resbox = self.do_transaction(command, None)

        if 'error' in resbox: raise OSError(resbox['error'])
        return

    def unlink(self, file):
        command = [
            {'type' : 'newop', 'op' : 'unlink'},
            {'type' : 'opparam', 'param' : 'file', 'value' : file},
            {'type' : 'startop'},
        ]
        resbox = self.do_transaction(command, None)

        if 'error' in resbox: raise OSError(resbox['error'])
        return

    def execute(self, args=[], stdout_cb=None, stderr_cb=None):
        def data_cb(box):
            if box['name'] == 'stdout': stdout_cb(box['data'])
            elif box['name'] == 'stderr': stderr_cb(box['data'])
            else: raise RuntimeError("unknown stream '%s'" % box['name'])

        resbox = self.do_transaction([
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
