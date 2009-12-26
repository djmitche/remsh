# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information

import unittest
import threading

from remsh.xport.local import LocalXport


class TestLocalXport(unittest.TestCase):
    def top_thread(self, top):
        top.write("chicken?")
        self.assertEqual(top.read(), "turkey")
        self.assertEqual(top.read(), "ham?")
        top.write("yep")
        top.close()

    def bottom_thread(self, bottom):
        self.assertEqual(bottom.read(), "chicken?")
        bottom.write("turkey")
        bottom.write("ham?")
        self.assertEqual(bottom.read(), "yep")
        self.assertEqual(bottom.read(), "")
        self.assertEqual(bottom.read(), "") # EOF is "sticky"

    def test_local(self):
        top, bottom = LocalXport.create()

        top_th = threading.Thread(target=self.top_thread, args=(top,))
        bottom_th = threading.Thread(target=self.bottom_thread, args=(bottom,))

        top_th.start()
        bottom_th.start()

        top_th.join()
        bottom_th.join()
