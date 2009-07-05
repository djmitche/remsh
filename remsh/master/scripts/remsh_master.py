# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information

import sys
import readline
import threading

from remsh.amp import wire
from remsh.master.slavecollection import simple
from remsh.master.slavelistener import tcp
    
def print_stream(data):
    sys.stdout.write(data)

def run_on_all(slaves, cmd):
    def run_on(slave, cmd):
        def print_stream(data):
            sys.stdout.write("%s: %s" % (slave.hostname, data))
        rc = slave.execute(args=['/bin/sh', '-c', cmd],
                stdout_cb=print_stream, stderr_cb=print_stream)

    # make a thread for each slave
    thds = [ threading.Thread(target=run_on, args=(sl, cmd)) for sl in slaves ]

    # start them
    for thd in thds: thd.start()

    # and join them
    for thd in thds: thd.join()

def main():
    coll = simple.SimpleSlaveCollection()
    listener = tcp.TcpSlaveListener(slave_collection=coll, port=int(sys.argv[1]))
    listener.start()

    done = False
    slave = None
    slavename = None
    while not done:
        slavenames = ", ".join(sl.hostname for sl in coll.get_all_slaves())
        cmd = raw_input("  slaves: %s\nremsh on %s> " % (slavenames, slavename,)).strip()
        if cmd.startswith('slave '):
            slavename = cmd[6:]
            slave = coll.get_slave(True, lambda sl : sl.hostname == slavename)
        elif cmd == "quit":
            done = True
        elif cmd == "cd":
            newdir = slave.set_cwd()
            print "now in %s" % newdir
        elif cmd.startswith("cd "):
            newdir = slave.set_cwd(cwd[3:])
            print "now in %s" % newdir
        elif cmd.startswith("all "):
            run_on_all(coll.get_all_slaves(), cmd[4:])
        elif cmd:
            if not slave:
                print "no slave"
                continue
            rc = slave.execute(args=['/bin/sh', '-c', cmd],
                    stdout_cb=print_stream, stderr_cb=print_stream)
            print "$? = %d" % rc

main()
