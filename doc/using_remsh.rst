***********
Using Remsh
***********

Remsh provides a synchronous, but thread-safe, interface to invoke operations
on slaves.

===============
Slave Listeners
===============

First, you'll need some way to connect to slaves.  Actually, in most cases the
slaves connect to the master, as a security measure: otherwise, any bug in
remsh's authentication would be equivalent to a wide-open back door!

Slave listeners are responsible for connecting new slaves to the master.
Several implementations are available, and a master can use any combination of
implementations.

Each slave listener class is implemented in its own module, and the modules
should ordinarily be imported directly, e.g., ::

    from remsh.master.slavelistener import tcp
    # ...
    listener = tcp.TcpSlaveListener(..)

.. class:: remsh.master.slavelistener.base.SlaveListener(slave_class=class, slave_collection=collection)

    :param slave_class: class to instantiate for new slaves (defaults to :class:`~remsh.master.slave.Slave`)
    :param slave_collection: slave collection object to which new slaves should be added (see below)

    This is the abstract base class for slave listeners.  All slave listener
    subclasses take the named parameters ``slave_class`` and
    ``slave_collection``.

    .. attribute:: slave_class

        The slave class given to the constructor

    .. attribute:: slave_collection

        The slave collection given to the constructor

.. class:: remsh.master.slavelistener.tcp.TcpSlaveListener(port=port, ...)

    :param port: TCP port on which to listen for incoming connections

    This is is a simple TCP-based listener that accepts incoming connections
    and spawns a new slave for each connection. 
    
    .. method:: start()

        Start the listening thread.  The port is not opened until this method is called.

.. class:: remsh.master.slavelistener.local.LocalSlaveListener(...)

    This class spawns slaves locally.  It is useful for testing and for executing operations
    locally, on the master.
    
    .. method:: start_slave(basedir)

        :param basedir: base directory for the new slave
        :returns: the slave object

        Start a new slave.

    .. method:: kill_slave(slave)

        :param slave: the slave object to kill

        Kill the slave, interrupting any operation it is performing.

=================
Slave Collections
=================

Next, you'll need to find a slave.  Slaves 
