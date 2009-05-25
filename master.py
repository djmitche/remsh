import sys
import time
import socket
import simpleamp
import threading

class ProtocolError(Exception):
    pass

class SlaveProtocol(threading.Thread):
    hosts = {}

    def __init__(self, conn):
        threading.Thread.__init__(self)
        self.setDaemon = True

        self.conn = conn
        self.version = -1
        self.hostname = None

        # condition variable for current_command, signalled
        # whenever the value changes from None to a Command
        self.cond = threading.Condition()
        self.current_command = None

        self.start()

    def do_command(self, command):
        self.cond.acquire()
        while self.current_command is not None:
            self.cond.wait()
        self.current_command = command
        self.cond.notifyAll()
        self.cond.release()

    def run(self):
        try:
            self.startup()
            self.loop()
        except:
            if self.hostname:
                del self.hosts[self.hostname]
            raise

    def startup(self):
        # first, get the registration box from the slave
        regbox = self.conn.read_box()
        if not regbox: return

        if regbox['type'] != 'register':
            raise ProtocolError("did not get 'register' box")

        self.version = regbox['version']
        self.hostname = regbox['hostname']
        SlaveProtocol.hosts[regbox['hostname']] = self

        self.setName("SlaveProtocol(%s)" % self.hostname)

        self.conn.send_box({'type' : 'registered'})

    def loop(self):
        while 1:
            print "waiting for command on", self.hostname

            self.cond.acquire()
            while self.current_command is None:
                self.cond.wait() # TODO: timeout with keepalives
            self.cond.release()

            # send the command as an op
            for box in self.current_command:
                self.conn.send_box(box)
            self.conn.send_box({'type' : 'startop'})

            # and read the results
            while 1:
                box = self.conn.read_box()
                if not box: raise ProtocolError("slave disconnected while running a command")
                if box['type'] == 'data':
                    print "%20s:%r" % (box['name'], box['data'])
                elif box['type'] == 'opdone':
                    print "result:", box['result']
                    break

            self.cond.acquire()
            self.current_command = None
            self.cond.notifyAll()
            self.cond.release()
        
def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    print "port:", s.getsockname()[1]

    while 1:
        sl_sock, sl_addr = s.accept()
        print "connection from", sl_addr
        conn = simpleamp.Connection(sl_sock)

        prot = SlaveProtocol(conn)

        time.sleep(1)
        prot.do_command([
            {'type' : 'newop', 'op' : 'shell' },
            {'type' : 'opparam', 'param' : 'arg', 'value' : 'cat' },
            {'type' : 'opparam', 'param' : 'arg', 'value' : '/etc/passwd' },
        ])

main()

