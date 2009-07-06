#!/usr/bin/env python
# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information

import sys
import socket

from remsh.amp import wire
from remsh.slave import dispatcher


def main():
    master = sys.argv[1]
    port = int(sys.argv[2])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((master, port))

    conn = wire.SimpleWire(s)
    dispatcher.run(conn)


main()
