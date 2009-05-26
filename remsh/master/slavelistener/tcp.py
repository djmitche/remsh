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
Implements a SlaveListener that listens on a TCP port for incoming connections.
"""

import sys
import os
import socket
import threading

from remsh import simpleamp
from remsh.master.slavelistener import base

class TcpSlaveListener(base.SlaveListener):
    """
    A listener in the truest sense: listens on a TCP port and spawns new slave
    objects for any incoming connection.
    """

    def __init__(self, slave_class=None, slave_collection=None, port=None):
        """
        Create a new listener withthe given slave class and collection, and listening
        on the given port.
        """
        base.SlaveListener.__init__(self,
            slave_collection=slave_collection, slave_class=slave_class)
        self.port = port
        self.thread = threading.Thread(target=self._run)
        self.thread.setDaemon(1)
        self.thread.setName("TcpSlaveListener on port %d" % port)

    def start(self):
        """
        Start listening for incoming connections.
        """
        self.thread.start()

    def _run(self):
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.bind(("", self.port))
        sk.listen(5)

        while 1:
            slavesock, slaveaddr = sk.accept()

            # set up the slave in a thread, since it may block
            def setup_slave():
                conn = simpleamp.Connection(slavesock)
                self.handle_new_connection(conn)
            slavethread = threading.Thread(target=setup_slave)
            slavethread.start()
