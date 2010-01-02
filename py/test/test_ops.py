# This file is part of remsh
# Copyright 2009, 2010 Dustin J. Mitchell
# See COPYING for license information

import unittest
import threading
import shutil
import os

from remsh.xport.local import LocalXport
from remsh.wire import Wire
from remsh.slave.server import SlaveServer
from remsh.master.remote import RemoteSlave, NotFoundError, \
                               FileExistsError, FailedError


class Ops(unittest.TestCase):
    # get this value at class initialization time, since we change the cwd
    # later
    basedir = os.path.abspath("optests")

    def setUpFilesystem(self):
        self.tearDownFilesystem()
        os.makedirs(self.basedir)
        os.chdir(self.basedir)

    def tearDownFilesystem(self):
        if not os.path.exists(self.basedir):
            return

        os.chdir("/")
        try:
            shutil.rmtree(self.basedir)
            return
        except OSError:
            pass

        # do a recursive chmod 0700 and try again
        for root, dirs, files in os.walk(self.basedir):
            for d in dirs:
                os.chmod(os.path.join(root, d), 0700)

        shutil.rmtree(self.basedir)

    def setUpSlave(self):
        self.slave_xport, self.master_xport = LocalXport.create()

        slave_wire = Wire(self.slave_xport)
        slave_server = SlaveServer(slave_wire)

        self.slave_server_thd = threading.Thread(target=slave_server.serve)
        self.slave_server_thd.setDaemon(1)
        self.slave_server_thd.start()

        master_wire = Wire(self.master_xport)
        self.slave = RemoteSlave(master_wire)

    def tearDownSlave(self):
        self.master_xport.close()
        self.slave_server_thd.join()

        self.slave_xport = self.master_xport = None
        self.slave_server_thd = None
        self.slave = None

    def setUp(self):
        self.clear_files()
        self.setUpFilesystem()
        self.setUpSlave()

    def tearDown(self):
        self.tearDownSlave()
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
        return lambda(data): self.files[file].append(data)

    ## tests

    def test_set_cwd(self):
        # set up directories first
        for subdir in ['a/1', 'a/2/b']:
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

        # invalid dir raises NotFoundError
        self.assertRaises(NotFoundError, lambda: self.slave.set_cwd("z"))

    def test_getenv(self):
        # slave environment should look just like our environment (TODO: if
        # this turns out to be fragile, then insert a specific value into the
        # env while launching the slave, and test for it here)
        env = self.slave.getenv()
        self.assertEqual(env, os.environ)

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
        self.assertEqual(os.stat(localfile).st_size,
            os.stat(destfile).st_size, "sizes match")

        self.assertRaises(FileExistsError,
            lambda: self.slave.send(localfile, destfile))

        os.unlink(destfile)
        os.unlink(localfile)

    def test_fetch(self):
        # prep
        srcfile = os.path.join(self.basedir, "srcfile")
        localfile = os.path.join(self.basedir, "localfile")

        # add some data to 'srcfile'
        f = open(srcfile, "w")
        d = "abc" * 10000
        for i in xrange(30):
            f.write(d)
        f.close()

        self.slave.fetch(srcfile, localfile)

        self.assert_(os.path.exists(localfile))
        self.assertEqual(os.stat(localfile).st_size,
            os.stat(srcfile).st_size, "sizes match")

        self.assertRaises(FileExistsError,
            lambda: self.slave.fetch(srcfile, localfile))

        self.assertRaises(NotFoundError,
            lambda: self.slave.fetch("/does/not/exist", localfile + "2"))

        self.assertRaises(IOError,
            lambda: self.slave.fetch(srcfile, "/does/not/exist"))

        os.unlink(srcfile)
        os.unlink(localfile)

    def test_remove(self):
        exists = os.path.join(self.basedir, "exists")
        missing = os.path.join(self.basedir, "missing")

        def prep():
            os.makedirs(exists)
            open(os.path.join(exists, "file1"), "w") # touch the file
            os.makedirs(os.path.join(exists, "dir"))
            open(os.path.join(exists, "dir", "file2"), "w")

        prep()
        self.slave.remove(exists)
        self.assert_(not os.path.exists(exists))

        # try again, with an unwriteable file
        prep()
        permprob = os.path.join(exists, "dir")
        os.chmod(permprob, 0) # remove write permission
        self.slave.remove(exists)
        self.assert_(not os.path.exists(exists))

        self.slave.remove(missing)
        # (doesn't raise an exception)

        existing_file = os.path.join(exists, "myfile")
        os.mkdir(exists)
        open(existing_file, "w")

        self.slave.remove(existing_file)
        self.assert_(not os.path.exists(existing_file))

    def test_rename(self):
        exists = os.path.join(self.basedir, "exists")
        open(exists, "w")
        missing = os.path.join(self.basedir, "missing")

        self.assertRaises(NotFoundError,
            lambda: self.slave.rename(missing, missing))
        self.assertRaises(FileExistsError,
            lambda: self.slave.rename(exists, exists))

        self.slave.rename(exists, missing)
        self.assert_(not os.path.exists(exists))
        self.assert_(os.path.exists(missing))

    def test_copy(self):
        exists = os.path.join(self.basedir, "exists")
        open(exists, "w")
        missing = os.path.join(self.basedir, "missing")

        self.assertRaises(NotFoundError,
            lambda: self.slave.copy(missing, missing))
        self.assertRaises(FileExistsError,
            lambda: self.slave.copy(exists, exists))

        self.slave.copy(exists, missing)
        self.assert_(os.path.exists(exists))
        self.assert_(os.path.exists(missing))

    def test_stat(self):
        missing = os.path.join(self.basedir, "missing")
        somedir = os.path.join(self.basedir, "somedir")
        somefile = os.path.join(somedir, "somefile")
        os.mkdir(somedir)
        open(somefile, "w")

        self.assertEquals(self.slave.stat(missing), '')
        self.assertEquals(self.slave.stat(somedir), 'd')
        self.assertEquals(self.slave.stat(somefile), 'f')
        os.chmod(somedir, 0) # remove r/x permission
        self.assertRaises(FailedError, lambda: self.slave.stat(somefile))
        os.chmod(somedir, 0777) # restore permission

if __name__ == '__main__':
    unittest.main()
