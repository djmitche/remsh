Python
======

This section describes the Python implemtation of remsh.

Remsh is packaged in the ``remsh`` namespace, and exposes symbols at particular
places in the hierarchy that are guaranteed to remain available.  This allows
flexibility to move modules around in the future without breaking links.

Transport Layer
---------------

The transport layer is in the ``remsh.xport`` namespace.  The ``base`` module
defines a the Python API for all transport classes, although it does not
implement any functionality.  Because Python is duck-typed, it's not critical
to inherit from this class, but it is a helpful indicator for other developers.

A "local" xport is available for testing purposes in ``remsh.xport.local``.
Objects of this type are created in pairs, similar to the ``pipe(2)`` function::

    from remsh.xport.local import LocalXport
    left, right = LocalXport.create()

Note that, because the transport API is blocking, these transport objects
cannot be used simultaneously in the same thread.
