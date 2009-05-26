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
Contains the L{SlaveCollection} base class.
"""

import threading

from zope.interface import implements

from remsh import interfaces

class SimpleSlaveCollection(object):
    """

    A simple L{ISlaveCollection} implementation which just keeps a dictionary of
    slaves, protected by a condition variable.

    """

    implements(interfaces.ISlaveConnection)

    def __init__(self):
        self.cond = threading.Condition()
        self.slaves = {}

    def add_slave(self, slave, listener):
        self.cond.acquire()
        assert slave.hostname not in self.slaves
        self.slaves[slave.hostname] = slave
        slave.on_disconnect(self._remove_slave)
        self.cond.notifyAll()
        self.cond.release()

    def _remove_slave(self, slave):
        self.cond.acquire()
        if slave.hostname in self.slaves:
            del self.slaves[slave.hostname]
        self.cond.notifyAll()
        self.cond.release()

    def get_slave(self, block, filter, cmp=None):
        """
        Get a slave matching ``filter`` (a callable).  If ``block`` is false
        and no connected slaves match the filter, then return None.  Otherwise,
        block until a matching slave appears.  If more than one matching slave
        is available, the slaves are sorted with ``cmp`` and the first slave
        returned.  If ``cmp`` is none, the slaves are shuffled randomly.
        """
        # TODO
