#! python
# This file is part of Remsh.
#
# Remsh is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Remsh is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Remsh.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import socket
import subprocess
import select

from remsh import simpleamp

def run(conn):
    """
    Run a slave on ``conn``, a L{simpleamp.Connection} object.  This function
    returns if the remote end disconnects cleanly.
    """
    conn.send_box({'type' : 'register', 'hostname' : socket.gethostname(), 'version' : 1})
    box = conn.read_box()
    if not box or box['type'] != 'registered':
        raise RuntimeError("expected a 'registered' box, got %s" % (box,))

    global default_wd
    default_wd = os.getcwd()

    while 1:
        box = conn.read_box()
        if not box:
            return
        if box['type'] != 'newop':
            raise RuntimeError("expected a 'newop' box")
        if box['op'] == 'execute':
            op_execute(conn)
        elif box['op'] == 'set_cwd':
            op_set_cwd(conn)
        elif box['op'] == 'mkdir':
            op_mkdir(conn)
        else:
            raise RuntimeError("unknown op '%s'" % box['op'])

def op_set_cwd(conn):
    new_cwd = None
    while 1:
        box = conn.read_box()
        if box['type'] == 'startop':
            break
        elif box['type'] == 'opparam':
            if box['param'] == 'cwd':
                new_cwd = box['value']
            else:
                raise RuntimeError("unknown set_cwd opparam '%s'" % box['param'])
        else:
            raise RuntimeError("unknown box type '%s'" % box['type'])

    if new_cwd is None:
        new_cwd = default_wd
    try:
        os.chdir(new_cwd)
        new_cwd = os.getcwd()
    except OSError:
        conn.send_box({'type' : 'opdone'})
        return

    conn.send_box({'type' : 'opdone', 'cwd' : new_cwd})

def op_mkdir(conn):
    dir = None
    while 1:
        box = conn.read_box()
        if box['type'] == 'startop':
            break
        elif box['type'] == 'opparam':
            if box['param'] == 'dir':
                dir = box['value']
            else:
                raise RuntimeError("unknown mkdir opparam '%s'" % box['param'])
        else:
            raise RuntimeError("unknown box type '%s'" % box['type'])

    if dir is None:
        raise RuntimeError("no 'dir' specified to mkdir op")
    try:
        os.makedirs(dir)
    except OSError, e:
        conn.send_box({'type' : 'opdone', 'error' : e.strerror})
        return

    conn.send_box({'type' : 'opdone', 'result' : 'OK'})

def op_execute(conn):
    args = []
    while 1:
        box = conn.read_box()
        if box['type'] == 'startop':
            break
        elif box['type'] == 'opparam':
            if box['param'] == 'arg':
                args.append(box['value'])
            else:
                raise RuntimeError("unknown execute opparam '%s'" % box['param'])
        else:
            raise RuntimeError("unknown box type '%s'" % box['type'])

    # run the command
    null = open("/dev/null")
    proc = subprocess.Popen(args=args,
        stdin=null, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True)

    # now use select to watch those files, with a short timeout to watch
    # for process exit
    timeout = 0.01
    readfiles = [proc.stdout, proc.stderr]
    while 1:
        rlist, wlist, xlist = select.select(readfiles, [], [], timeout)
        timeout = min(1.0, timeout * 2)
        def send(file, name):
            data = file.read(65535)
            if not data:
                readfiles.remove(file)
            else:
                conn.send_box({'type' : 'data', 'name' : name, 'data' : data})
        if proc.stdout in rlist: send(proc.stdout, 'stdout')
        if proc.stderr in rlist: send(proc.stderr, 'stderr')
        if not rlist and proc.poll() is not None: break
    conn.send_box({'type' : 'opdone', 'result' : proc.returncode})
    
