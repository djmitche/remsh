import sys
import socket
import subprocess
import select
import simpleamp

def register(conn):
    conn.send_box({'type' : 'register', 'hostname' : socket.gethostname(), 'version' : 1})
    box = conn.read_box()
    if not box or box['type'] != 'registered':
        raise RuntimeError("expected a 'registered' box")

def run(conn):
    while 1:
        print "waiting for command"
        box = conn.read_box()
        if not box or box['type'] != 'newop':
            raise RuntimeError("expected a 'newop' box")
        if box['op'] == 'shell':
            op_shell(conn)
        else:
            raise RuntimeError("unknown op '%s'" % box['op'])

def op_shell(conn):
    args = []
    while 1:
        box = conn.read_box()
        if box['type'] == 'startop':
            break
        elif box['type'] == 'opparam':
            if box['param'] == 'arg':
                args.append(box['value'])
            else:
                raise RuntimeError("unknown shell opparam '%s'" % box['param'])
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
        print "timeout", timeout
        print "poll", proc.poll()
        rlist, wlist, xlist = select.select(readfiles, [], [], timeout)
        print "select returned", rlist, wlist, xlist
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
    
def main():
    master = sys.argv[1]
    port = int(sys.argv[2])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((master, port))

    conn = simpleamp.Connection(s)
    register(conn)
    run(conn)

main()
