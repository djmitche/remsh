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

Implements a "local" SlaveListener which spawns a fixed number
of local slaves.  Mostly useful for testing.

"""

import sys
import os
import signal
import socket
import traceback

from remsh.amp import wire
from remsh.master.slavelistener import base
from remsh.slave import dispatcher

class LocalSlaveListener(base.SlaveListener):
    def __init__(self, slave_class=None, slave_collection=None):
        base.SlaveListener.__init__(self,
            slave_collection=slave_collection, slave_class=slave_class)

        self._slave_pids = {} # keyed by id(slave)

    def start_slave(self, basedir):
        assert(os.path.exists(basedir))
        parsock, kidsock = socket.socketpair()

        pid = os.fork()
        if pid != 0:
            # parent
            kidsock.close()
            conn = wire.SimpleWire(parsock)
            slave = self.handle_new_connection(conn)

            self._slave_pids[id(slave)] = pid

            return slave

        # child
        try:
            parsock.close()
            os.chdir(basedir)
            conn = wire.SimpleWire(kidsock)
            dispatcher.run(conn)
        except KeyboardInterrupt:
            pass
        except:
            print >>sys.stderr, "EXCEPTION IN LOCAL CHILD:"
            traceback.print_exc()
        finally:
            os._exit(1)

    def kill_slave(self, slave):
        if id(slave) in self._slave_pids:
            pid = self._slave_pids[id(slave)]
            os.kill(pid, signal.SIGKILL)
