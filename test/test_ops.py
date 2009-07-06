# This file is part of remsh
# Copyright 2009 Dustin J. Mitchell
# See COPYING for license information

import unittest
import shutil
import os

from remsh.amp.rpc import RemoteError
from remsh.master.slavelistener import local
from remsh.master.slavecollection import simple

class OpsTestMixin(object):
    def setUpFilesystem(self):
        self.tearDownFilesystem()
        os.makedirs(self.basedir)

    def tearDownFilesystem(self):
        if os.path.exists(self.basedir):
            shutil.rmtree(self.basedir)

    def setUp(self):
        self.basedir = os.path.abspath("optests")

        self.clear_files()
        self.setUpFilesystem()
        self.slave = self.setUpSlave() # supplied by mixin

    def tearDown(self):
        self.tearDownSlave(self.slave) # supplied by mixin
        self.tearDownFilesystem()

    ## data callbacks

    def clear_files(self):
        self.files = {}

    def get_file(self, file, join_chunks=True):
        if join_chunks:
            return ''.join(self.files[file])
        else:
            return self.files[file]

    def make_callback(self, file):
        self.files[file] = []
        def cb(data):
            self.files[file].append(data)
        return cb

    ## tests

    def test_mkdir(self):
        newdir = os.path.join(self.basedir, "newdir")
        self.assert_(not os.path.exists(newdir))
        self.slave.mkdir("newdir")
        self.assert_(os.path.exists(newdir))

        # should not fail if the directory already exists
        self.slave.mkdir("newdir")
        self.assert_(os.path.exists(newdir))

        # nested directories
        nested = os.path.join(self.basedir, "nested/bested/quested")
        self.assert_(not os.path.exists(nested))
        self.slave.mkdir("nested/bested/quested")
        self.assert_(os.path.exists(nested))

    def test_set_cwd(self):
        # set up directories first
        for subdir in [ 'a/1', 'a/2/b' ]:
            os.makedirs(os.path.join(self.basedir,
                *tuple(subdir.split('/'))))

        # set_cwd() should revert to basedir
        newcwd = self.slave.set_cwd()
        self.assertEqual(newcwd, self.basedir)

        # relative to base dir
        newcwd = self.slave.set_cwd("a")
        self.assertEqual(newcwd, os.path.join(self.basedir, "a"))

        # relative to previous dir
        newcwd = self.slave.set_cwd("1")
        self.assertEqual(newcwd, os.path.join(self.basedir, "a", "1"))

        # just fetch the cwd
        newcwd = self.slave.set_cwd("")
        self.assertEqual(newcwd, os.path.join(self.basedir, "a", "1"))

        # '..' works
        newcwd = self.slave.set_cwd("../2/b")
        self.assertEqual(newcwd, os.path.join(self.basedir, "a", "2", "b"))

        # revert to basedir again
        newcwd = self.slave.set_cwd(None)
        self.assertEqual(newcwd, self.basedir)

        # invalid dir raises RemoteError
        self.assertRaises(RemoteError, lambda : self.slave.set_cwd("z"))

    def test_unlink(self):
        # prep
        exists = os.path.join(self.basedir, "exists")
        missing = os.path.join(self.basedir, "missing")
        open(exists, "w")

        self.slave.unlink("exists")
        self.assert_(not os.path.exists(exists))

        self.assertRaises(RemoteError, lambda : self.slave.unlink(missing))

    def test_execute(self):
        # note that all of these tests are just using 'sh'

        # simple shell exit status
        result = self.slave.execute(args=['sh', '-c', 'exit 0'])
        self.assertEqual(result, 0)
        result = self.slave.execute(args=['sh', '-c', 'exit 10'])
        self.assertEqual(result, 10)

        def execute_output(command_str, stdout='', stderr=''):
            self.clear_files()
            result = self.slave.execute(args=['sh', '-c', command_str],
                stderr_cb=self.make_callback('stderr'),
                stdout_cb=self.make_callback('stdout'))
            self.assertEqual(result, 0, "result from '%s'" % command_str)
            self.assertEqual(self.get_file('stdout').strip(), stdout,
                    "stdout from '%s'" % command_str)
            self.assertEqual(self.get_file('stderr').strip(), stderr,
                    "stderr from '%s'" % command_str)

        execute_output('echo "hello"', stdout="hello")
        execute_output('echo "oh noes" >&2', stderr="oh noes")
        execute_output('echo "yes"; echo "no" >&2', stdout="yes", stderr="no")

    def test_send(self):
        # prep
        destfile = os.path.join(self.basedir, "destfile")
        localfile = os.path.join(self.basedir, "localfile")

        # add some data to 'localfile'
        f = open(localfile, "w")
        d = "abc" * 10000
        for i in xrange(30):
            f.write(d)
        f.close()

        self.slave.send(localfile, destfile)

        self.assert_(os.path.exists(destfile))
        self.assertEqual(os.stat(localfile).st_size, os.stat(destfile).st_size, "sizes match")

        self.assertRaises(RemoteError, lambda : self.slave.send(localfile, destfile))

        os.unlink(destfile)
        os.unlink(localfile)

class LocalSlaveMixin(object):
    def setUpSlave(self):
        self.slave_collection=simple.SimpleSlaveCollection()

        self.listener = local.LocalSlaveListener(slave_collection=self.slave_collection)
        self.listener.start_slave(self.basedir)

        return self.slave_collection.get_slave(block=True, filter=lambda sl : True)

    def tearDownSlave(self, slave):
        self.listener.kill_slave(self.slave)
        self.listener = None

class TestLocalOps(LocalSlaveMixin, OpsTestMixin, unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()
