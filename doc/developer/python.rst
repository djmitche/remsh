Python
======

This section describes the Python implemtation of remsh.

Remsh is packaged in the ``remsh`` namespace, and exposes symbols at particular
places in the hierarchy that are guaranteed to remain available.  This allows
flexibility to move modules around in the future without breaking links.

Transport Layer
---------------

The transport layer is in the ``remsh.xport`` namespace.  The ``base`` module
defines a the Python API for all transport classes, in the form of a base
class.

A "local" xport is available for testing purposes in ``remsh.xport.local``.
Objects of this type are created in pairs, similar to the ``pipe(2)`` function::

    from remsh.xport.local import LocalXport
    left, right = LocalXport.create()

Note that, because the transport API is blocking, these transport objects
cannot be used simultaneously in the same thread.

Wire Layer
----------

The wire layer is in the ``remsh.wire`` namespace.  Since there is only one
wire implementation, this is implemented as a module, and exposes the class
with the name ``remsh.wire.Wire``.

Note that boxes are represented as simple Python dictionaries, the keys and
values of which are stringified if necessary.  The ``read_box`` method returns
``None`` if it receives an EOF between boxes, and otherwise raises
``EOFError``.  The ``remsh.wire.Error`` exception class is used to indicate
protocol-specific errors.

Operations Layer
----------------

The operations layer is not symmetrical, so it has distinct implementations on
the master and slave sides.  These are embedded in the ``remsh.master`` and
``remsh.slave`` namespaces, respectively, which also contain the mechanics of
usable Python applications.

Master Operations
.................

TODO

Slave Operations
................
