#! python
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

import os
import sys
import socket
import subprocess
import select

from remsh import simpleamp
from remsh.slave import ops

def run(conn):
    """
    Run a slave on ``conn``, a L{simpleamp.Connection} object.  This function
    returns if the remote end disconnects cleanly.
    """
    conn.send_box({'type' : 'register', 'hostname' : socket.gethostname(), 'version' : 1})
    box = conn.read_box()
    if not box or box['type'] != 'registered':
        raise RuntimeError("expected a 'registered' box, got %s" % (box,))

    ops.default_wd = os.getcwd()

    while 1:
        box = conn.read_box()
        if not box:
            return
        if box['type'] != 'newop':
            raise RuntimeError("expected a 'newop' box")
        if box['op'] not in ops.functions:
            raise RuntimeError("unknown op '%s'" % box['op'])
        ops.functions[box['op']](conn)
