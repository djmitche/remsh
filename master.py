import sys
import time
import socket
import slavemgr
import time


def main():
    slavemgr.SlaveManager().start()

    while 1:
        time.sleep(5)

main()
