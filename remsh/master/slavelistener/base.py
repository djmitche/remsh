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
Implements a base class for SlaveListeners
"""

import sys

from zope.interface import implements

from remsh import interfaces
from remsh import simpleamp
from remsh.master import slave

class SlaveListener(object):
    implements(interfaces.ISlaveListener)

    def __init__(self, slave_collection=None, slave_class=None):
        if slave_class:
            self.slave_class = slave_class
        else:
            self.slave_class = slave.Slave

        assert slave_collection is not None
        self.slave_collection = slave_collection

    def handle_new_connection(self, conn):
        # TODO: how are exceptions handled?

        # read the registration box
        regbox = conn.read_box()
        if not regbox: return # TODO: exception?

        if regbox['type'] != 'register':
            raise ProtocolError("did not get 'register' box")
        hostname = regbox['hostname']
        version = int(regbox['version'])

        conn.send_box({'type' : 'registered'})

        slave = self.slave_class(conn, hostname, version)

        slave.setup()

        self.slave_collection.add_slave(slave, self)
        return slave
