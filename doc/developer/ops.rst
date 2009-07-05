Operations
==========

This section describes the RPC call or calls for each Remsh operation.  In each
case, only the method-specific box keys are described.

set_cwd
-------

The request box has the following key.

``cwd``
    requested new working directory; this may be a partial path, in which case
    it is relative to the current directory

If the ``cwd`` key is omitted, then the request is to revert to the default
working directory.  An empty (but present) ``cwd`` is a request to return the
current directory without changing it.

The response box has the following key.

``cwd``
    resulting working directory; this should be an absolute path

mkdir
-----

The request box has the following key:

``dir``
    directory to create

The response box is empty.

unlink
------

The request box has the following key:

``file``
    file to unlink

The response box is empty.

execute
-------

The request box has the following keys:

``args``
    list of command-line arguments, separated with 0 bytes.

``want_stdout``
    ``y`` if ``data`` calls should be made with data from stdout, otherwise
    ``n``

``want_stderr``
    ``y`` if ``data`` calls should be made with data from stderr, otherwise
    ``n``

The response is an empty box.  After the response, the slave side makes zero or
more ``data`` calls, none of which require a response, and exactly one
``finished`` call, which also does not require a response.  A ``data`` request
represents some quantity of output data from the spawned process, and has the
following keys:

``stream``
    the name of the stream that produced the data (``stderr`` and ``stdout``
    are the standard streams)

``data``
    one or more bytes of data

The ``finished`` request has the following key:

``result``
    exit value for this process, in decimal notation

TODO
''''

* optionally translate platform-specific newlines to '\n'
* provide a more generic list-of-strings thing, and quote NUL bytes in it
* support additional watched files
