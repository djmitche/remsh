# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information
"""
Implements a base class for SlaveListeners
"""

import sys

from remsh.amp.rpc import RPC
from remsh.master import slave


class SlaveListener(object):

    def __init__(self, slave_collection=None, slave_class=None):
        if slave_class:
            self.slave_class = slave_class
        else:
            self.slave_class = slave.Slave

        assert slave_collection is not None
        self.slave_collection = slave_collection

    def handle_new_connection(self, wire):
        # TODO: how are exceptions handled?

        # read the registration box
        regbox = wire.read_box()
        if not regbox:
            return # TODO: exception?

        if regbox['type'] != 'register':
            raise ProtocolError("did not get 'register' box")
        hostname = regbox['hostname']
        version = int(regbox['version'])

        wire.send_box({'type': 'registered'})

        slave = self.slave_class(wire, hostname, version)

        slave.setup()

        self.slave_collection.add_slave(slave, self)
        return slave
