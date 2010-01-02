# This file is part of remsh
# Copyright 2009, 2010 Dustin J. Mitchell
# See COPYING for license information

import sys
import readline
import socket

from remsh.xport.fd import FDXport
from remsh.wire import Wire
from remsh.master.remote import RemoteSlave


def print_stream(data):
    sys.stdout.write(data)


def run_on_all(sslavelaves, cmd):

    def run_on(slave, cmd):

        def print_stream(data):
            sys.stdout.write("%s: %s" % (slave.hostname, data))

        rc = slave.execute(args=['/bin/sh', '-c', cmd],
                stdout_cb=print_stream, stderr_cb=print_stream)

    # make a thread for each slave
    thds = [threading.Thread(target=run_on, args=(sl, cmd)) for sl in slaves]

    # start them
    for thd in thds:
        thd.start()

    # and join them
    for thd in thds:
        thd.join()


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    print "connect to port %d" % s.getsockname()[1]

    s.listen(5)
    subsock, addr = s.accept()
    s.close()
    rem = RemoteSlave(Wire(FDXport(subsock.fileno())))
    print "connected"

    done = False
    while not done:
        cmd = raw_input("remsh> ")
        if cmd == "quit":
            done = True
        elif cmd == "cd":
            newdir = rem.set_cwd()
            print "now in %s" % newdir
        elif cmd.startswith("cd "):
            newdir = rem.set_cwd(cmd[3:])
            print "now in %s" % newdir
        elif cmd:
            rc = rem.execute(args=['/bin/sh', '-c', cmd],
                    stdout_cb=print_stream, stderr_cb=print_stream)
            print "$? = %d" % rc

if __name__ == "__main__":
    main()
