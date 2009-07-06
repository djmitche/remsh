# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information
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
                acceptable = [slave for slave in self.slaves.itervalues() if filter(slave)]
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
