.. _slave_collections:

*****************
Slave Collections
*****************

A slave collection manages the set of available slaves on the master.  Slaves may
be added by any number of slave listeners (see :ref:`slave_listeners`).

=======================
Simple Slave Collection
=======================

.. class:: remsh.master.slavecollection.simple.SimpleSlaveCollection()

    This is a simple slave collection implementation which just keeps a
    thread-safe dictionary of slaves.  It does not support any kind of
    "reservation" of slaves.

    .. method:: add_slave(slave, listener)

        :param slave: slave object to add to the collection
        :param listener: the slave listener object that connected this slave

        Add the given slave to the collection.

    .. method:: get_slave(block, filter[, cmp])

        :param block: should this call block if no suitable slave is available?
        :param filter: callable to identify suitable slaves
        :param cmp: comparison function to sort suitable slaves

        Get a slave matching `filter`.  If `block` is false and no connected
        slaves match the filter, then return `None`.  Otherwise, block until a
        matching slave appears.  If more than one matching slave is available,
        the slaves are sorted with `cmp` and the first slave returned.  If
        `cmp` is none, the slaves are shuffled randomly.

    .. method:: get_all_slaves()

       :returns: a list of Slave objects

       Get all of the currently available slaves
