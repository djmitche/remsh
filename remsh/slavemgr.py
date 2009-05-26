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

Implements the master side of the remsh protocol:

"""

import sys
import time
import socket
import threading

from remsh import simpleamp

class ProtocolError(Exception):
    pass

class SlaveProtocol(threading.Thread):
    def __init__(self, conn, slavemgr):
        threading.Thread.__init__(self)
        self.setDaemon = True

        self.conn = conn
        self.slavemgr = slavemgr
        self.version = -1
        self.hostname = None

        # condition variable for current_command, signalled
        # whenever the value changes from None to a Command
        self.cond = threading.Condition()
        self.current_command = None

    def do_command(self, command):
        self.cond.acquire()
        while self.current_command is not None:
            self.cond.wait()
        self.current_command = command
        self.cond.notifyAll()
        self.cond.release()

    def run(self):
        try:
            self.startup()
            self.loop()
        except:
            if self.hostname:
                self.slavemgr.remove_slave(self.hostname)
            raise

    def startup(self):
        # first, get the registration box from the slave
        regbox = self.conn.read_box()
        if not regbox: return

        if regbox['type'] != 'register':
            raise ProtocolError("did not get 'register' box")

        self.version = regbox['version']
        self.hostname = regbox['hostname']
        self.slavemgr.add_slave(self.hostname, self)

        self.setName("SlaveProtocol(%s)" % self.hostname)

        self.conn.send_box({'type' : 'registered'})

    def loop(self):
        while 1:
            print "waiting for command on", self.hostname

            self.cond.acquire()
            while self.current_command is None:
                self.cond.wait() # TODO: timeout with keepalives
            self.cond.release()

            # send the command as an op
            for box in self.current_command:
                self.conn.send_box(box)
            self.conn.send_box({'type' : 'startop'})

            # and read the results
            while 1:
                box = self.conn.read_box()
                if not box: raise ProtocolError("slave disconnected while running a command")
                if box['type'] == 'data':
                    print "%20s:%r" % (box['name'], box['data'])
                elif box['type'] == 'opdone':
                    print "result:", box['result']
                    break

            self.cond.acquire()
            self.current_command = None
            self.cond.notifyAll()
            self.cond.release()
        
class SlaveManager(threading.Thread):
    """

    Manage a collection of slaves.  This should be defined by an interface,
    with some mixins to listen on different protocols (socket, ssl + cert
    checking, etc.), authentication, and methods to call on slaves connecting
    and disconnecting.

    """
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.setDaemon(1)
        self.setName("SlaveManager")

        self.port = port

        self.slaves_cond = threading.Condition()
        self.slaves = {}

    def add_slave(self, hostname, slave):
        self.slaves_cond.acquire()
        assert hostname not in self.slaves
        self.slaves[hostname] = slave
        self.slaves_cond.release()

    def remove_slave(self, hostname):
        self.slaves_cond.acquire()
        if hostname in self.slaves:
            del self.slaves[hostname]
        self.slaves_cond.release()

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", self.port))
        s.listen(1)

        while 1:
            sl_sock, sl_addr = s.accept()
            conn = simpleamp.Connection(sl_sock)

            SlaveProtocol(conn, self).start()
