.. _slaves:

Operations
**********

The primary purpose of Remsh is to perform operations on remote systems.  The
interface to those remote operations is the :class:`~remsh.master.slave.Slave`
class.  Each instance of this class represents a distinct remote system, and
that system can perform at most one operation at any given time.


.. class:: remsh.master.slave.Slave(wire, hostname, version)

    :param wire: :class:`~remsh.amp.wire.SimpleWire` instance this slave should use
    :param hostname: hostname of the slave
    :param version: protocol version the slave supplied

    Slave objects give access to all of the operations supported by remsh.
    Note that these operations all block, first waiting for any already-running
    operations to finish, and then waiting for the requested operation to
    finish.  To support concurrent use of multiple slaves, invoke operations
    from different Python threads on the master.

    The class is designed to be easily subclassed by users, but only one
    implementation is included with Remsh.

    Any of the following operation methods may raise
    :class:`~remsh.amp.rpc.RemoteError`, :class:`~remsh.amp.wire.Error`, or
    :class:`socket.error`.

    .. method:: set_cwd(cwd=None)

        :param cwd: directory to switch to, or None for basedir

        Sets the working directory of the slave, returning the new working
        directory.  Raises an :class:`~remsh.amp.rpc.RemoteError` if the
        designated directory is not found.  The pathname is treated as a simple
        bytestring, to be interepreted by the slave.

        If `cwd` is None, then this method resets the working directory to the
        slave's base directory.  Note that such an invocation may still raise
        :class:`~remsh.amp.rpc.RemoteError`, if the slave's base directory has
        been deleted.

        if `cwd` is an empty string, then no directory change takes place, and
        the method returns the current directory.

    .. method:: getenv()

        :returns: the slave environment as a dictionary

        Get all environment variables on the slave which might be sent to a
        child process.  Note that the slave environment cannot be edited, but
        may be overridden on each invocation of :meth:`execute`.

    .. method:: mkdir(dir)

        :param dir: directory to create (relative or absolute)

        Does the equivalent of ``mkdir -p`` on the remote system.  Raises an
        :class:`~remsh.amp.rpc.RemoteError` in the event of an error on the
        slave side.  It is *not* an error to create a directory that already
        exists.

    .. method:: unlink(file)

        :param file: the file to unlink

        Deletes the given file, raising a :class:`~remsh.amp.rpc.RemoteError`
        in the event of an error.  It is an error to delete a file that does
        not exist.

    .. method:: execute(args=[], stdout_cb=None, stderr_cb=None)
        
        :param args: sequence of command-line arguments
        :param stdout_cb: callback for stdout data
        :param stderr_cb: callback for stderr data
        :returns: process exit code (0 generally meaning success)

        Execute `args` in a subprocess.

        If `stdout_cb` is not None, it is called for each "chunk" of the
        executable's standard output seen; `stderr_cb` does the same for
        standard error.

    .. method:: send(src, dest)

        :param src: source filename (on the master)
        :param dest: destination filename (on the slave)

        Copies `src`, on the master, to `dest` on the slave.  This is a basic,
        data-only copy, so no file metadata, "forks", "streams", or anything
        like that will be copied.  The destination filename can be relative to
        the current directory or absolute.

        This method raises :class:`~remsh.amp.rpc.RemoteError` if `dest`
        already exists.

    .. method:: fetch(src, dest)

        :param src: source filename (on the slave)
        :param dest: destination filename (on the master)

        Copies `src`, on the slave, to `dest` on the master.  Like
        :meth:`send`, this is a data-only copy.  The source filename can be
        relative to the current directory or absolute.  

        This method raises :class:`~remsh.amp.rpc.RemoteError` if `src` does
        not exist or is not readable, or if `dest` already exists.

    .. method:: remove(path)

        :param path: path to the file or directory to remove

        Remove `path` and all files and directories beneath it.  This method is
        most often used for cleanup, so it tries everything possible (including
        resetting subdirectory permissions) to delete the file or directory,
        but raises :class:`~remsh.amp.rpc.RemoteError` if it is not successful.

        This method will succeed trivially if `path` does not exist.

    .. method:: rename(src, dest)

        :param src: file or directory to rename
        :param dest: destination filename (must not already exist)

        Rename `src` to `dest`, subject to any local restrictions on renames
        across filesystems.  Raises :class:`~remsh.amp.rpc.RemoteError` if the
        operation is not successful.

    .. method:: stat(pathname)

        :param pathname: pathname to stat
        :returns: ``"d"`` or ``"f"`` or ``None``

        Check the given pathname for existence, and return ``"d"`` for a
        directory, ``"f"`` for a file (actually, anything but a directory), or
        ``None`` if the path does not exist.  Raises
        :class:`~remsh.amp.rpc.RemoteError` if a permission error prevents the
        check.

    The Slave class also implements a few utility methods:

    .. method:: setup()

        This method is a hook, called after the slave has registered, but
        before it is added to the slave collection. The method is called in its
        own thread, and can do whatever additional setup is required, including
        executing operations on the slave.  One possibility is to dynamically
        investigate the capabilities of the slave for later use.  Another is to
        set up periodic commands, e.g. keepalives or load monitoring.  These
        should run in a separate thread.

    .. method:: on_disconnect(callable)

        :param callable: invoked when the slave disconnects

        Register `callable` to be called when this slave disconnects,
        whether smoothly or in the midst of an operation.  Slave collection
        objects (see :ref:`slave_collections`) should use this to mark the
        slave as no longer available.  The callable is invoked with the
        :class:`Slave` instance as its argument.
