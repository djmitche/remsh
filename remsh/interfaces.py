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

from zope.interface import Interface, Attribute

class ISlaveCollection(Interface):
    """
    I collect Slave objects.
    """
    def add_slave(name, slave, listener):
        """
        Add SLAVE, named NAME and connected via LISTENER, to the collection.
        This method must be thread-safe.
        """

class ISlaveListener(Interface):
    """
    I listen for incoming connections from slaves and instantiate new L{ISlave}
    providers, then hand them off to an L{ISlaveCollection}.
    """

    slave_collection = Attribute("""
    L{ISlaveCollection} object to which new objects are added.
    """)

    slave_class = Attribute("""
    Class to instantiate for each new slave.  This class must implement L{ISlave}.
    """)

class ISlave(Interface):
    """

    I represent a remote slave, and provide methods to execute operations on
    those slaves.  Note that operations will block the current thread.

    There are actually two potentially blocking activities: first, the slave
    must be "available" - not executing some other operation.  Operation
    methods will always block until the slave is available.  It is up to the
    caller to ensure that this does not cause deadlock.  Second, the thread
    will block while the operation is being executed on the remote slave.
    """

    def __init__(ampconn, hostname, version):
        """
        Create a new slave object, using ``ampconn``.  The hostname and version
        have already been determined from the registration process.
        """

    def setup():
        """
        A "hook", called after the slave has registered, but before it is given
        to the L{ISlaveCollection}. This method can do whatever additional
        setup is required, including executing operations on the slave.  One
        possibility is to dynamically investigate the capabilities of the slave
        for later use.  Another is to set up periodic commands, e.g. keepalives
        or load monitoring.  These should run in a separate thread.

        This method is called in a thread, and can block for as long as
        desired.  Note that it is called by the L{ISlaveListener}.
        """

    def set_cwd(new_cwd=None):
        """
        Set the working directory of the slave, returning the new working
        directory or None if the directory does not exist.

        If ``new_cwd`` is None, then this method resets the working directory
        to the slave's "default" directory.

        The pathname is treated as a simple bytestring, to be interepreted
        by the slave.
        """

    # TODO: mkdir, unlink, rmtree, rename, copy(?), upload, download

    def execute(args=[], stdout_cb=None, stderr_cb=None):
        """

        Execute 'args' in a forked child.

        If ``stdout_cb`` is not None, it is called for each "chunk" of the
        executable's standard output seen; ``stderr_cb`` does the same for
        standard error.

        Returns the exit status of the command.

        """
        # TODO: interpet exit status on slave side
        # TODO: environment
        # TODO: stdin (streaming)
        # TODO: other params

    def on_disconnect(callable):
        """
        Register ``callable`` to be called when this slave disconnects, whether
        smoothly or in the midst of an operation.  L{ISlaveCollection} objects
        should use this to mark the slave as no longer available.  ``Callable``
        is invoked with the L{ISlave} instance as its argument.
        """
