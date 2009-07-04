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
Contains the L{SlaveCollection} base class.
"""

import threading
import random

class SimpleSlaveCollection(object):
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

    def get_all_slaves(self):
        return self.slaves.values()

    def get_slave(self, block, filter, cmp=None):
        self.cond.acquire()
        try:
            while 1:
                acceptable = [ slave for slave in self.slaves.itervalues() if filter(slave) ]
                if len(acceptable) == 0:
                    if block:
                        self.cond.wait()
                        continue
                    else:
                        return None
                if cmp:
                    acceptable.sort(cmp)
                else:
                    random.shuffle(acceptable)
                return acceptable[0]
        finally:
            self.cond.release()
