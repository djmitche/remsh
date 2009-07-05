# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information

"""
Implements a SlaveListener that listens on a TCP port for incoming connections.
"""

import sys
import os
import socket
import threading

from remsh.amp import wire
from remsh.master.slavelistener import base

class TcpSlaveListener(base.SlaveListener):
    def __init__(self, slave_class=None, slave_collection=None, port=None):
        base.SlaveListener.__init__(self,
            slave_collection=slave_collection, slave_class=slave_class)
        self.port = port
        self.thread = threading.Thread(target=self._run)
        self.thread.setDaemon(1)
        self.thread.setName("TcpSlaveListener on port %d" % port)

    def start(self):
        self.thread.start()

    def _run(self):
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sk.bind(("", self.port))
        sk.listen(5)

        while 1:
            slavesock, slaveaddr = sk.accept()

            # set up the slave in a thread, since it may block
            def setup_slave():
                w = wire.SimpleWire(slavesock)
                self.handle_new_connection(w)
            slavethread = threading.Thread(target=setup_slave)
            slavethread.start()
