# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information

import os
import Queue

from remsh.xport.base import Error, Xport


class LocalXport(Xport):
    """

    A process-local transport; created in pairs by the 'create' class method.

    """

    @classmethod
    def create(cls):
        up = Queue.Queue()
        down = Queue.Queue()
        top = cls(up, down)
        bottom = cls(down, up)
        return (top, bottom)

    def __init__(self, input_queue, output_queue):
        self.input_queue = input_queue
        self.output_queue = output_queue

    def read(self):
        rv = self.input_queue.get()
        if not rv:
            # re-push the EOF
            self.input_queue.put(rv)
        return rv

    def write(self, data):
        if data:
            self.output_queue.put(data)

    def close(self):
        self.input_queue = None
        self.output_queue.put('')
        self.output_queue = None
