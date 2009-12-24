# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information


class Error(Exception):
    "Transport-layer error"


class Xport(object):
    """

    Base class for transport object; a cheap form of interface

    """

    def read(self):
        """

        Read and return as much data as is available from the incoming
        bytestream, blocking until at least one byte is available; returns
        an empty string on EOF.

        """

    def write(self, data):
        """

        Write all bytes of DATA to the connection, blocking until all bytes
        have been transmitted (but not necessarily received on the remote
        side).

        """

    def close(self):
        """

        Close the connection.

        """
