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

    def remove_slave(name):
        """
        Remote slave named NAME.  This method must be thread-safe.
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
    those slaves, either synchronously (calling thread blocks until the
    operation is completed) or asynchronously (invoking a callable when the
    operation is complete).

    There are actually two potentially blocking operations: first, the slave
    must be "available" - not executing some other operation.  Operation
    methods will always block if the slave is not available, so it is up to the
    caller to ensure only one thread is trying to use a slave at any time.

    Second, the thread may block while the operation is being executed on the
    remote slave.  If the ``result_cb`` parameter is not None, the operation
    methods will return immediately, and will invoke ``result_cb`` in another
    thread when the operation is complete.

    A ``result_cb`` is always called with the value that would otherwise be
    returned by the method.  In the case that this is a tuple, each tuple
    element is provided as a distinct argument to ``result_cb``.

    """

    def set_cwd(new_cwd=None, result_cb=None):
        """
        Set the working directory of the slave, returning the new working
        directory or None if the directory does not exist.

        If ``new_cwd`` is None, then this method resets the working directory
        to the slave's "default" directory.

        Relative pathnames are allowed.
        """
        # TODO: encoding
        # TODO: os-dependent separators

    # TODO: mkdir, unlink, rmtree, rename, copy(?), upload, download

    def execute(args=[], stdout_cb=None, stderr_cb=None, result_cb=None):
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
