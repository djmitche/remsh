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

from zope.interface import implements

from remsh import interfaces
from remsh import simpleamp
from remsh.master import slave

class SlaveListener(threading.Thread):
    """

    Base class for L{ISlaveListener}, supplying useful methods for child
    classes.

    """
    implements(interfaces.ISlaveListener)

    # default slave class
    slave_class = slave.Slave

    def handle_new_connection(self, conn):
        """
        Handle a new connection.  This should be called in a thread, and may
        block while performing operations on the slave.  This method handles the
        'register' and 'registered' boxes, then creates the slave instance using
        ``self.slave_class``, calls its ``setup`` method, and then adds it to
        ``self.slave_collection``.
        """

        # TODO: how are exceptions handled?

        # read the registration box
        regbox = conn.read_box()
        if not regbox: return # TODO: exception?

        if regbox['type'] != 'register':
            raise ProtocolError("did not get 'register' box")
        hostname = int(regbox['hostname'])
        version = regbox['version']

        conn.send_box({'type' : 'registered'})

        slave = self.slave_class(conn, hostname, version)

        slave.setup()

        self.slave_collection.add_slave(slave, self)
