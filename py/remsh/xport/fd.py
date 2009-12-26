# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information

import os

from remsh.xport.base import Error, Xport


class FDXport(Xport):
    """

    Base class for file-descriptor-based transports.  Not for use by users.

    """

    def __init__(self, fd):
        self.fd = fd

    def read(self):
        return os.read(self.fd, 32768)

    def write(self, data):
        while data:
            bcount = os.write(self.fd, data)
            if bcount < len(data):
                data = data[bcount:]
            else:
                break

    def close(self):
        os.close(self.fd)
        self.fd = -1

    def __del__(self):
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1
