#!/usr/bin/env python
# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information

import sys
import socket

from remsh.xport.fd import FDXport
from remsh.wire import Wire
from remsh.slave.server import SlaveServer


def usage():
    print "USAGE: %s master-hostname master-port"
    sys.exit(1)


def main():
    if len(sys.argv) != 3:
        usage()
    master = sys.argv[1]
    try:
        port = int(sys.argv[2])
    except ValueError:
        usage()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((master, port))

    svr = SlaveServer(Wire(FDXport(s.fileno())))
    svr.serve()

if __name__ == "__main__":
    main()
